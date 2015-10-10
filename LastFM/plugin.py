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

from __future__ import unicode_literals
import supybot.utils as utils
from supybot.commands import *
import supybot.conf as conf
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
import supybot.log as log

from xml.dom import minidom
from time import time
try:
    from itertools import izip # Python 2
except ImportError:
    izip = zip # Python 3
import pickle

class LastFMDB():
    """Holds the LastFM IDs of all known nicks

    (This database is case insensitive and channel independent)
    """

    def __init__(self, *args, **kwargs):
        self.db = {}
        try:
            with open(filename, 'rb') as f:
               self.db = pickle.load(f)
        except Exception as e:
            log.debug('LastFM: Unable to load database, creating '
                      'a new one: %s', e)

    def flush(self):
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self.db, f, 2)
        except Exception as e:
            log.warning('LastFM: Unable to write database: %s', e)

    def set(self, prefix, newId):
        user = prefix.split('!', 1)[1]
        self.db[user] = newId

    def get(self, prefix):
        user = prefix.split('!', 1)[1]
        try:
            return self.db[user]
        except:
            return # entry does not exist

class LastFMParser:
    def parseRecentTracks(self, stream):
        """
        <stream>

        Returns a tuple with the information of the last-played track.
        """
        xml = minidom.parse(stream).getElementsByTagName("recenttracks")[0]
        user = xml.getAttribute("user")

        try:
            t = xml.getElementsByTagName("track")[0] # most recent track
        except IndexError:
            return [user] + [None]*5
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
    threaded = True

    def __init__(self, irc):
        self.__parent = super(LastFM, self)
        self.__parent.__init__(irc)
        self.db = LastFMDB(filename)
        world.flushers.append(self.db.flush)

        # 2.0 API (see http://www.lastfm.de/api/intro)
        self.apiKey = self.registryValue("apiKey")
        self.APIURL = "http://ws.audioscrobbler.com/2.0/?"

    def die(self):
        world.flushers.remove(self.db.flush)
        self.db.flush()
        self.__parent.die()

    def nowPlaying(self, irc, msg, args, user):
        """[<user>]

        Announces the track currently being played by <user>. If <user>
        is not given, defaults to the LastFM user configured for your
        current nick.
        """
        if not self.apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)
        user = (user or self.db.get(msg.prefix) or msg.nick)

        # see http://www.lastfm.de/api/show/user.getrecenttracks
        url = "%sapi_key=%s&method=user.getrecenttracks&user=%s" % (self.APIURL, self.apiKey, user)
        try:
            f = utils.web.getUrlFd(url)
        except utils.web.Error:
            irc.error("Unknown user '%s'." % user, Raise=True)

        parser = LastFMParser()
        (user, isNowPlaying, artist, track, album, time) = parser.parseRecentTracks(f)
        if track is None:
            irc.reply("%s doesn't seem to have listened to anything." % user)
            return
        albumStr = ("[%s]" % album) if album else ""
        track, artist, albumStr = map(ircutils.bold, (track, artist, albumStr))
        if isNowPlaying:
            irc.reply('%s is listening to %s by %s %s'
                    % (ircutils.bold(user), track, artist, albumStr))
        else:
            irc.reply('%s listened to %s by %s %s more than %s'
                    % (ircutils.bold(user), track, artist, albumStr,
                        self._formatTimeago(time)))

    np = wrap(nowPlaying, [optional("something")])

    def setUserId(self, irc, msg, args, newId):
        """<user>

        Sets the LastFM username for the caller and saves it in a database.
        """

        self.db.set(msg.prefix, newId)
        irc.replySuccess()

    set = wrap(setUserId, ["something"])

    def profile(self, irc, msg, args, user):
        """[<user>]

        Prints the profile info for the specified LastFM user. If <user>
        is not given, defaults to the LastFM user configured for your
        current nick.
        """
        if not self.apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)
        user = (user or self.db.get(msg.prefix) or msg.nick)

        url = "%sapi_key=%s&method=user.getInfo&user=%s" % (self.APIURL, self.apiKey, user)
        try:
            f = utils.web.getUrlFd(url)
        except utils.web.Error:
            irc.error("Unknown user '%s'." % user, Raise=True)

        xml = minidom.parse(f).getElementsByTagName("user")[0]
        keys = ("realname", "registered", "age", "gender", "country", "playcount")
        profile = {"id": ircutils.bold(user)}
        for tag in keys:
            try:
                profile[tag] = ircutils.bold(xml.getElementsByTagName(tag)[0].firstChild.data.strip())
            except AttributeError: # empty field
                profile[tag] = ircutils.bold('unknown')
        irc.reply(("%(id)s (realname: %(realname)s) registered on %(registered)s; age: %(age)s / %(gender)s; "
                  "Country: %(country)s; Tracks played: %(playcount)s") % profile)

    profile = wrap(profile, [optional("something")])

    def _formatTimeago(self, unixtime):
        t = int(time()-unixtime)
        if t/86400 >= 1:
            return "%i days ago" % (t/86400)
        if t/3600 >= 1:
            return "%i hours ago" % (t/3600)
        if t/60 >= 1:
            return "%i minutes ago" % (t/60)
        if t > 0:
            return "%i seconds ago" % (t)

filename = conf.supybot.directories.data.dirize("LastFM.db")

Class = LastFM


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
