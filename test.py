###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class WeatherTestCase(PluginTestCase):
    plugins = ('Weather',)

    def setUp(self):
        PluginTestCase.setUp(self)
        conf.supybot.plugins.Weather.apiKey.setValue('fc7cb609a45365fa')

    def testWeather(self):
        self.assertSnarfResponse('reload Weather', 'The operation succeeded.')
        self.assertRegexp('wunderground 10002', 'New York, NY')
        self.assertSnarfResponse('setweather 10002', "I have changed test's weather ID to 10002")
        self.assertSnarfResponse('setuser metric True', "I have changed test's metric setting to 1")
        self.assertRegexp('wunderground', 'New York, NY')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
