###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class WeatherTestCase(PluginTestCase):
    plugins = ('Weather',)
    #config = {'supybot.plugins.Weather.apiKey':'fc7cb609a45365fa'}

    def setUp(self):
        PluginTestCase.setUp(self)
        conf.supybot.plugins.Weather.apiKey.setValue('fc7cb609a45365fa')

    def testWeather(self):
        self.assertSnarfResponse('reload Weather', 'The operation succeeded.')
        self.assertRegexp('wunderground 10002', 'New York, NY')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
