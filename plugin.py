###
# Copyright (c) 2006, Ilya Kuznetsov
# Copyright (c) 2008,2012 Kevin Funk
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.log as log

import urllib2
from xml.dom import minidom
from time import time

from LastFMDB import *

class LastFMParser:

    def parseRecentTracks(self, stream):
        """
        @return Tuple with track information of last track
        """

        xml = minidom.parse(stream).getElementsByTagName("recenttracks")[0]
        user = xml.getAttribute("user")

        t = xml.getElementsByTagName("track")[0] # most recent track
        isNowPlaying = (t.getAttribute("nowplaying") == "true")
        if not isNowPlaying:
            time = int(t.getElementsByTagName("date")[0].getAttribute("uts"))
        else:
            time = None

        artist = t.getElementsByTagName("artist")[0].firstChild.data
        track = t.getElementsByTagName("name")[0].firstChild.data
        try:
            albumNode = t.getElementsByTagName("album")[0].firstChild
            album = albumNode.data
        except (IndexError, AttributeError):
            album = None
        return (user, isNowPlaying, artist, track, album, time)

class LastFM(callbacks.Plugin):
    # 1.0 API (deprecated)
    APIURL_1_0 = "http://ws.audioscrobbler.com/1.0/user"

    # 2.0 API (see http://www.lastfm.de/api/intro)
    APIKEY = "b7638a70725eea60737f9ad9f56f3099"
    APIURL_2_0 = "http://ws.audioscrobbler.com/2.0/?api_key=%s&" % APIKEY

    def __init__(self, irc):
        self.__parent = super(LastFM, self)
        self.__parent.__init__(irc)
        self.db = LastFMDB(dbfilename)
        world.flushers.append(self.db.flush)

    def die(self):
        if self.db.flush in world.flushers:
            world.flushers.remove(self.db.flush)
        self.db.close()
        self.__parent.die()

    def lastfm(self, irc, msg, args, method, optionalId):
        """<method> [<id>]

        Lists LastFM info where <method> is in
        [friends, neighbours, profile, recenttracks, tags, topalbums,
        topartists, toptracks].
        Set your LastFM ID with the set method (default is your current nick)
        or specify <id> to switch for one call.
        """

        id = (optionalId or self.db.getId(msg.nick) or msg.nick)
        channel = msg.args[0]
        maxResults = self.registryValue("maxResults", channel)
        method = method.lower()

        url = "%s/%s/%s.txt" % (self.APIURL_1_0, id, method)
        try:
            f = urllib2.urlopen(url)
        except urllib2.HTTPError:
            irc.error("Unknown ID (%s) or unknown method (%s)"
                    % (msg.nick, method))
            return


        lines = f.read().split("\n")
        content = map(lambda s: s.split(",")[-1], lines)

        irc.reply("%s's %s: %s (with a total number of %i entries)"
                % (id, method, ", ".join(content[0:maxResults]),
                    len(content)))

    lastfm = wrap(lastfm, ["something", optional("something")])

    def nowPlaying(self, irc, msg, args, optionalId):
        """[<id>]

        Announces the now playing track of the specified LastFM ID.
        Set your LastFM ID with the set method (default is your current nick)
        or specify <id> to switch for one call.
        """

        id = (optionalId or self.db.getId(msg.nick) or msg.nick)

        # see http://www.lastfm.de/api/show/user.getrecenttracks
        url = "%s&method=user.getrecenttracks&user=%s" % (self.APIURL_2_0, id)
        try:
            f = urllib2.urlopen(url)
        except urllib2.HTTPError:
            irc.error("Unknown ID (%s)" % id)
            return

        parser = LastFMParser()
        (user, isNowPlaying, artist, track, album, time) = parser.parseRecentTracks(f)
        albumStr = "[" + album + "]" if album else ""
        if isNowPlaying:
            irc.reply(('%s is listening to "%s" by %s %s'
                    % (user, track, artist, albumStr)).encode("utf8"))
        else:
            irc.reply(('%s listened to "%s" by %s %s more than %s'
                    % (user, track, artist, albumStr,
                        self._formatTimeago(time))).encode("utf-8"))

    np = wrap(nowPlaying, [optional("something")])

    def setUserId(self, irc, msg, args, newId):
        """<id>

        Sets the LastFM ID for the caller and saves it in a database.
        """

        self.db.set(msg.nick, newId)

        irc.reply("LastFM ID changed.")
        self.profile(irc, msg, args)

    set = wrap(setUserId, ["something"])

    def profile(self, irc, msg, args, optionalId):
        """[<id>]

        Prints the profile info for the specified LastFM ID.
        Set your LastFM ID with the set method (default is your current nick)
        or specify <id> to switch for one call.
        """

        id = (optionalId or self.db.getId(msg.nick) or msg.nick)

        url = "%s/%s/profile.xml" % (self.APIURL_1_0, id)
        try:
            f = urllib2.urlopen(url)
        except urllib2.HTTPError:
            irc.error("Unknown user (%s)" % id)
            return

        xml = minidom.parse(f).getElementsByTagName("profile")[0]
        keys = "realname registered age gender country playcount".split()
        profile = tuple([self._parse(xml, node) for node in keys])

        irc.reply(("%s (realname: %s) registered on %s; age: %s / %s; \
Country: %s; Tracks played: %s" % ((id,) + profile)).encode("utf8"))

    profile = wrap(profile, [optional("something")])

    def compareUsers(self, irc, msg, args, user1, optionalUser2):
        """user1 [<user2>]

        Compares the taste from two users
        If <user2> is ommitted, the taste is compared against the ID of the calling user.
        """

        user2 = (optionalUser2 or self.db.getId(msg.nick) or msg.nick)

        channel = msg.args[0]
        maxResults = self.registryValue("maxResults", channel)
        # see http://www.lastfm.de/api/show/tasteometer.compare
        url = "%s&method=tasteometer.compare&type1=user&type2=user&value1=%s&value2=%s&limit=%s" % (
            self.APIURL_2_0, user1, user2, maxResults
        )
        try:
            f = urllib2.urlopen(url)
        except urllib2.HTTPError, e:
            irc.error("Failure: %s" % (e))
            return

        xml = minidom.parse(f)
        resultNode = xml.getElementsByTagName("result")[0]
        score = float(self._parse(resultNode, "score"))
        scoreStr = "%s (%s)" % (round(score, 2), self._formatRating(score))
        # Note: XPath would be really cool here...
        artists = [el for el in resultNode.getElementsByTagName("artist")]
        artistNames = [el.getElementsByTagName("name")[0].firstChild.data for el in artists]
        irc.reply(("Result of comparison between %s and %s: score: %s, common artists: %s" \
                % (user1, user2, scoreStr, ", ".join(artistNames))
            ).encode("utf-8")
        )

    compare = wrap(compareUsers, ["something", optional("something")])

    def _parse(self, node, tagName, exceptMsg="not specified"):
            try:
                return node.getElementsByTagName(tagName)[0].firstChild.data
            except IndexError:
                return exceptMsg

    def _formatTimeago(self, unixtime):
        t = int(time()-unixtime)
        if t/86400 > 0:
            return "%i days ago" % (t/86400)
        if t/3600 > 0:
            return "%i hours ago" % (t/3600)
        if t/60 > 0:
            return "%i minutes ago" % (t/60)
        if t > 0:
            return "%i seconds ago" % (t)

    def _formatRating(self, score):
        """Format rating

        @param score Value in the form of [0:1] (float)
        """

        if score >= 0.9:
            return "Super"
        elif score >= 0.7:
            return "Very High"
        elif score >= 0.5:
            return "High"
        elif score >= 0.3:
            return "Medium"
        elif score >= 0.1:
            return "Low"
        else:
            return "Very Low"

dbfilename = conf.supybot.directories.data.dirize("LastFM.db")

Class = LastFM


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
