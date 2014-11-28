###
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

from supybot.test import *
from .plugin import LastFMParser

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

class LastFMTestCase(PluginTestCase):
    plugins = ('LastFM',)

    def setUp(self):
        PluginTestCase.setUp(self)
        apiKey = os.environ.get('lastfm_apikey')
        if not apiKey:
            e = ("The LastFM API key has not been set. "
            "Please set the environment variable 'lastfm_apikey' "
            "and try again. ('export lastfm_apikey=<apikey>' for those "
            "using bash)")
            raise callbacks.Error(e)
        conf.supybot.plugins.LastFM.apiKey.setValue(apiKey)

    def testLastfm(self):
        self.assertNotError("lastfm recenttracks")
        self.assertError("lastfm TESTEXCEPTION")
        self.assertNotError("lastfm recenttracks czshadow")
        self.assertNotError("lastfm np krf")

    def testLastfmDB(self):
        self.assertNotError("lastfm set nick") # test db
        self.assertNotError("lastfm set test") # test db unset

    def testLastfmProfile(self):
        self.assertNotError("lastfm profile czshadow")
        self.assertNotError("lastfm profile test")

    def testLastfmCompare(self):
        self.assertNotError("lastfm compare krf czshadow")
        self.assertNotError("lastfm compare krf")

    def testLastFMParseRecentTracks(self):
        """Parser tests"""

        # noalbum, nowplaying
        data1 = """<recenttracks user="USER" page="1" perPage="10" totalPages="3019">
  <track nowplaying="true">
    <artist mbid="2f9ecbed-27be-40e6-abca-6de49d50299e">ARTIST</artist>
    <name>TRACK</name>
    <mbid/>
    <album mbid=""/>
    <url>www.last.fm/music/Aretha+Franklin/_/Sisters+Are+Doing+It+For+Themselves</url>
    <date uts="1213031819">9 Jun 2008, 17:16</date>
    <streamable>1</streamable>
  </track>
</recenttracks>"""

        # album, not nowplaying
        data2 = """<recenttracks user="USER" page="1" perPage="10" totalPages="3019">
  <track nowplaying="false">
    <artist mbid="2f9ecbed-27be-40e6-abca-6de49d50299e">ARTIST</artist>
    <name>TRACK</name>
    <mbid/>
    <album mbid="">ALBUM</album>
    <url>www.last.fm/music/Aretha+Franklin/_/Sisters+Are+Doing+It+For+Themselves</url>
    <date uts="1213031819">9 Jun 2008, 17:16</date>
    <streamable>1</streamable>
  </track>
</recenttracks>"""

        parser = LastFMParser()
        (user, isNowPlaying, artist, track, album, time) = \
            parser.parseRecentTracks(StringIO(data1))
        self.assertEqual(user, "USER")
        self.assertEqual(isNowPlaying, True)
        self.assertEqual(artist, "ARTIST")
        self.assertEqual(track, "TRACK")
        self.assertEqual(album, None)
        self.assertEqual(time, None)

        (user, isNowPlaying, artist, track, album, time) = \
            parser.parseRecentTracks(StringIO(data2))
        self.assertEqual(album, "ALBUM")
        self.assertEqual(time, 1213031819)


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
