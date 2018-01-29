###
# Copyright (c) 2012-2014, spline
# Copyright (c) 2018, James Lu <james@overdrivenetworks.com>

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###

from supybot.test import *
import os

class WeatherTestCase(PluginTestCase):
    plugins = ('Weather',)

    def setUp(self):
        PluginTestCase.setUp(self)
        apiKey = os.environ.get('weather_apikey')
        if not apiKey:
            e = """The Wunderground API key has not been set.
            please set this value correctly via the environment variable
            "weather_apikey"."""
            raise Exception(e)
        conf.supybot.plugins.Weather.apiKey.setValue(apiKey)

    def testWeatherBasic(self):
        self.assertRegexp('weather New York City', 'New York, NY')
        self.assertError('weather InvalidLocationTestCasePleaseIgnore')

    def testWeatherUSZIPCode(self):
        self.assertRegexp('weather 10002', 'New York, NY')

    def testWeatherAmbiguous(self):
        # Returns Albany, NY last time I checked (2017-01-28)
        self.assertRegexp('weather New York', ', NY')
        # Alturas, CA (2017-01-28)
        self.assertRegexp('weather california', ', CA')
        # I'll be very upset if this returns the wrong one ;)
        self.assertRegexp('weather Vancouver', 'Vancouver, British Columbia')

    def testWeatherAirport(self):
        # IATA codes (e.g. YVR, PEK, LAX for these 3) are unreliable and
        # sometimes clash with other places
        self.assertRegexp('weather CYVR', 'Vancouver International')
        self.assertRegexp('weather ZBAA', 'Beijing Capital')
        self.assertRegexp('weather KLAX', 'Los Angeles International')

    def testWeatherSavesLocation(self):
        self.assertNotError('setweather 10002')
        self.assertNotError('setuser metric True')
        self.assertRegexp('weather', 'New York, NY')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
