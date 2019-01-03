###
# Copyright (c) 2006, Ilya Kuznetsov
# Copyright (c) 2008,2012 Kevin Funk
# Copyright (c) 2014-2019 James Lu <james@overdrivenetworks.com>
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
import supybot.ircdb as ircdb

import json
from datetime import datetime
from .local import accountsdb

class LastFM(callbacks.Plugin):
    threaded = True

    def __init__(self, irc):
        self.__parent = super(LastFM, self)
        self.__parent.__init__(irc)
        self.db = accountsdb.AccountsDB("LastFM", "LastFM.db", self.registryValue(accountsdb.CONFIG_OPTION_NAME))
        world.flushers.append(self.db.flush)

        # 2.0 API (see http://www.lastfm.de/api/intro)
        self.APIURL = "http://ws.audioscrobbler.com/2.0/?"

    def die(self):
        world.flushers.remove(self.db.flush)
        self.db.flush()
        self.__parent.die()

    @wrap([optional("something")])
    def np(self, irc, msg, args, user):
        """[<user>]

        Announces the track currently being played by <user>. If <user>
        is not given, defaults to the LastFM user configured for your
        current nick.
        """
        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)
        user = (user or self.db.get(msg.prefix) or msg.nick)

        # see http://www.lastfm.de/api/show/user.getrecenttracks
        url = "%sapi_key=%s&method=user.getrecenttracks&user=%s&format=json" % (self.APIURL, apiKey, user)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown user %s." % user, Raise=True)
        self.log.debug("LastFM.nowPlaying: url %s", url)

        try:
            data = json.loads(f)["recenttracks"]
        except KeyError:
            irc.error("Unknown user %s." % user, Raise=True)

        user = data["@attr"]["user"]
        tracks = data["track"]

        # Work with only the first track.
        try:
            trackdata = tracks[0]
        except IndexError:
            irc.error("%s doesn't seem to have listened to anything." % user, Raise=True)

        artist = trackdata["artist"]["#text"].strip()  # Artist name
        track = trackdata["name"].strip()  # Track name
        # Album name (may or may not be present)
        album = trackdata["album"]["#text"].strip()
        if album:
            album = ircutils.bold("[%s]" % album)

        try:
            time = int(trackdata["date"]["uts"])  # Time of last listen
            # Format this using the preferred time format.
            tformat = conf.supybot.reply.format.time()
            time = "at %s" % datetime.fromtimestamp(time).strftime(tformat)
        except KeyError:  # Nothing given by the API?
            time = "just now"

        public_url = ''
        # If the DDG plugin from this repository is loaded, we can integrate
        # that by finding a YouTube link for the track.
        if self.registryValue("fetchYouTubeLink", msg.args[0]):
            ddg = irc.getCallback("DDG")
            if ddg:
                try:
                    results = ddg.search_core('site:youtube.com "%s - %s"' % (artist, track),
                                              channel_context=msg.args[0], max_results=1, show_snippet=False)
                    if results:
                        public_url = format('%u', results[0][2])
                except:
                    # If something breaks, log the error but don't cause the
                    # entire np request to fail.
                    log.exception("LastFM: failed to get YouTube link for track %s - %s", artist, track)

        ext_info = ''
        if self.registryValue("showExtendedInfo", msg.args[0]):
            # Get extended info via a separate API call.
            ext_info_url = "%sapi_key=%s&method=track.getinfo&user=%s&format=json&artist=%s&track=%s" % (self.APIURL, apiKey, user,
                utils.web.urlquote(artist), utils.web.urlquote(track))
            ext_info_f = utils.web.getUrl(ext_info_url).decode("utf-8")
            self.log.debug("LastFM.nowPlaying: using url %s for extended info", ext_info_url)
            try:
                ext_data = json.loads(ext_info_f)['track']

                # We currently show play count and tags - more could be added in the future...
                userplaycount = ext_data['userplaycount']
                tags = [tag['name'] for tag in ext_data['toptags']['tag']]
                ext_info = ' (Playcount: %s / Tags: %s)' % (userplaycount, ', '.join(tags) or 'N/A')
            except KeyError:
                pass

        s = '%s listened to %s by %s %s %s%s. %s' % (ircutils.bold(user), ircutils.bold(track),
            ircutils.bold(artist), album, time, ext_info, public_url)
        irc.reply(utils.str.normalizeWhitespace(s))

    @wrap(["something"])
    def set(self, irc, msg, args, newId):
        """<user>

        Sets the LastFM username for the caller and saves it in a database.
        """

        self.db.set(msg.prefix, newId)
        irc.replySuccess()

    @wrap([optional("something")])
    def profile(self, irc, msg, args, user):
        """[<user>]

        Prints the profile info for the specified LastFM user. If <user>
        is not given, defaults to the LastFM user configured for your
        current nick.
        """
        apiKey = self.registryValue("apiKey")
        if not apiKey:
            irc.error("The API Key is not set. Please set it via "
                      "'config plugins.lastfm.apikey' and reload the plugin. "
                      "You can sign up for an API Key using "
                      "http://www.last.fm/api/account/create", Raise=True)
        user = (user or self.db.get(msg.prefix) or msg.nick)

        url = "%sapi_key=%s&method=user.getInfo&user=%s&format=json" % (self.APIURL, apiKey, user)
        self.log.debug("LastFM.profile: url %s", url)
        try:
            f = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error:
            irc.error("Unknown user '%s'." % user, Raise=True)

        data = json.loads(f)
        keys = ("realname", "age", "gender", "country", "playcount")
        profile = {"id": ircutils.bold(user)}
        for tag in keys:
            try:
                s = data["user"][tag] or "N/A"
                if tag == "age" and s == "0":
                    s = "N/A"
                elif tag == "gender" and s == "n":
                    s = "N/A"
            except KeyError: # empty field
                s = "N/A"
            finally:
                profile[tag] = ircutils.bold(s)
        try:
            # LastFM sends the user registration time as a unix timestamp;
            # Format it using the preferred time format.
            time = int(data["user"]["registered"]["unixtime"])
            tformat = conf.supybot.reply.format.time()
            s = datetime.fromtimestamp(time).strftime(tformat)
        except KeyError:
            s = "N/A"
        finally:
            profile["registered"] = ircutils.bold(s)
        irc.reply("%(id)s (realname: %(realname)s) registered on %(registered)s; age: %(age)s; gender: %(gender)s; "
                  "Country: %(country)s; Tracks played: %(playcount)s" % profile)

Class = LastFM


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
