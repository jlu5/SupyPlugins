###
# Copyright (c) 2008,2012 Kevin Funk
# Copyright (c) 2014-2015 James Lu
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
import os

class LastFMTestCase(PluginTestCase):
    plugins = ('LastFM',)

    def setUp(self):
        PluginTestCase.setUp(self)
        self.prefix = "a!b@c.d"
        apiKey = os.environ.get('lastfm_apikey')
        if not apiKey:
            e = ("The LastFM API key has not been set. "
                 "Please set the environment variable 'lastfm_apikey' "
                 "and try again.")
            raise callbacks.Error(e)
        conf.supybot.plugins.LastFM.apiKey.setValue(apiKey)

    def testNowPlaying(self):
        self.assertNotError("np krf")

    def testLastfmDB(self):
        self.assertNotError("lastfm set GLolol") # test db
        self.assertNotError("np")

    def testProfile(self):
        self.assertNotError("profile czshadow")
        self.assertNotError("profile test")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
