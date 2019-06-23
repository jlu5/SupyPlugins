###
# Copyright (c) 2019, James Lu <james@overdrivenetworks.com>
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

import unittest

from supybot.test import *
from supybot import log
from . import config

NO_NETWORK_REASON = "Network-based tests are disabled by --no-network"

class NuWeatherDarkSkyTestCase(PluginTestCase):
    plugins = ('NuWeather',)
    BACKEND = 'darksky'

    # These tests are not meant to be exhaustive, since we don't want to be hitting our
    # API limits :(

    def setUp(self):
        super().setUp()
        self.myVerbose = verbosity.MESSAGES  # Enable verbose logging of messages

        if not network:
            return  # Nothing to do if we've disabled network access

        # Fetch our API key
        varname = 'NUWEATHER_APIKEY_%s' % self.BACKEND.upper()
        apikey = os.environ.get(varname)
        if apikey:
            log.info('NuWeather: Set API key for %s from env var %s', self.BACKEND, varname)
            conf.supybot.plugins.NuWeather.apikeys.get(self.BACKEND).setValue(apikey)
        else:
            raise RuntimeError("Please set the %r environment variable to run this test" % varname)

        # Update default backend
        conf.supybot.plugins.NuWeather.defaultbackend.setValue(self.BACKEND)

    @unittest.skipUnless(network, NO_NETWORK_REASON)
    def testWeather(self):
        self.assertRegexp('weather Vancouver', 'Vancouver, British Columbia')
        self.assertRegexp('weather LAX', 'Los Angeles')
        #self.assertRegexp('weather 76010', 'Arlington')  # US ZIP codes not supported by Nominatim (default)
        self.assertError('weather InvalidLocationTest')

    @unittest.skipUnless(network, NO_NETWORK_REASON)
    def testSavedLocation(self):
        self.assertError('weather')  # No location set
        self.assertNotError('setweather Berlin')
        self.assertRegexp('weather', 'Berlin')

class NuWeatherApixuTestCase(NuWeatherDarkSkyTestCase):  # inherit settings from above
    BACKEND = 'apixu'

# TODO: test geocode backends

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
