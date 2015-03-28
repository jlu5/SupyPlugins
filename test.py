###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
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

    def testWeather(self):
        self.assertRegexp('weather 10002', 'New York, NY')
        self.assertNotError('setweather 10002')
        self.assertNotError('setuser metric True')
        self.assertRegexp('weather', 'New York, NY')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
