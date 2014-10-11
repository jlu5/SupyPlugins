###
# Copyright (c) 2012-2014, spline
# All rights reserved.
#
#
###

from supybot.test import *

class WeatherTestCase(PluginTestCase):
    plugins = ('Weather',)

    def testWeather(self):
        self.assertRegexp('wunderground 10002', 'New York, NY')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
