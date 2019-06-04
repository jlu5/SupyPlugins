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

import os

from supybot import callbacks
from supybot.test import *

class AQITestCase(PluginTestCase):
    plugins = ('AQI',)

    if network:
        def setUp(self):
            super().setUp()

            self.myVerbose = verbosity.MESSAGES

            apikey = os.environ.get('AQICN_APIKEY')
            if not apikey:
                e = ("The aqicn API key has not been set. Please set the AQICN_APIKEY environment variable "
                     "and try again.")
                raise callbacks.Error(e)

            conf.supybot.plugins.AQI.apikey.setValue(apikey)

        def testAQI(self):
            self.assertNotError("aqi Beijing")
            self.assertNotError("aqi --geocode-backend native Los Angeles")

            # This will fail because we have not loaded NuWeather
            self.assertError("aqi --geocode-backend nominatim Chengdu")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
