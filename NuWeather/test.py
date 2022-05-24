###
# Copyright (c) 2019-2020, James Lu <james@overdrivenetworks.com>
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

NO_NETWORK_REASON = "Network-based tests are disabled by --no-network"
class NuWeatherTestCase():
    plugins = ('NuWeather',)

    # These tests are not meant to be exhaustive, since I don't want to hit my free tier
    # API limits :(

    def setUp(self):
        PluginTestCase.setUp(self)
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
        self.assertRegexp('weather Vancouver', 'Vancouver,')
        self.assertRegexp('weather LAX', 'Los Angeles')
        #self.assertRegexp('weather 76010', 'Arlington')  # US ZIP codes not supported by Nominatim (default)
        self.assertError('weather InvalidLocationTest')

    @unittest.skipUnless(network, NO_NETWORK_REASON)
    def testSavedLocation(self):
        self.assertError('weather')  # No location set
        self.assertNotError('setweather Berlin')
        self.assertRegexp('weather', 'Berlin')

class NuWeatherDarkSkyTestCase(NuWeatherTestCase, PluginTestCase):
    BACKEND = 'darksky'

class NuWeatherWeatherstackTestCase(NuWeatherTestCase, PluginTestCase):
    BACKEND = 'weatherstack'

class NuWeatherOpenWeatherMapTestCase(NuWeatherTestCase, PluginTestCase):
    BACKEND = 'openweathermap'

from . import formatter

class NuWeatherFormatterTestCase(unittest.TestCase):
    def test_format_temp(self):
        func = formatter.format_temp
        self.assertEqual(func(f=50, c=10), '\x030950.0F/10.0C\x03')
        self.assertEqual(func(f=100), '\x0304100.0F/37.8C\x03')
        self.assertEqual(func(c=25.55), '\x030878.0F/25.6C\x03')
        self.assertEqual(func(), 'N/A')

    def test_format_temp_displaymode(self):
        func = formatter.format_temp
        with conf.supybot.plugins.NuWeather.units.temperature.context('F/C'):
            self.assertEqual(func(c=-5.3), '\x031022.5F/-5.3C\x03')
        with conf.supybot.plugins.NuWeather.units.temperature.context('C/F'):
            self.assertEqual(func(f=50, c=10), '\x030910.0C/50.0F\x03')
        with conf.supybot.plugins.NuWeather.units.temperature.context('C'):
            self.assertEqual(func(c=36), '\x030436.0C\x03')
        with conf.supybot.plugins.NuWeather.units.temperature.context('F'):
            self.assertEqual(func(f=72), '\x030872.0F\x03')

    def test_format_distance_speed(self):
        func = formatter.format_distance
        self.assertEqual(func(mi=123), '123mi/197.9km')
        self.assertEqual(func(km=42.6), '26.5mi/42.6km')
        self.assertEqual(func(mi=26, km=42), '26mi/42km')
        self.assertEqual(func(mi=0), '0')  # special case
        self.assertEqual(func(), 'N/A')

    def test_format_default(self):
        data = {'location': "Narnia",
                'poweredby': 'Dummy',
                'url': 'http://dummy.invalid/api/',
                'current': {
                    'condition': 'Sunny',
                    'temperature': formatter.format_temp(f=80),
                    'feels_like': formatter.format_temp(f=85),
                    'humidity': formatter.format_percentage(0.8),
                    'precip': formatter.format_precip(mm=90),
                    'wind': formatter.format_distance(mi=12, speed=True),
                    'wind_gust': formatter.format_distance(mi=20, speed=True),
                    'wind_dir': formatter.wind_direction(15),
                    'uv': formatter.format_uv(6),
                    'visibility': formatter.format_distance(mi=1000),
                },
                'forecast': [{'dayname': 'Today',
                            'max': formatter.format_temp(f=100),
                            'min': formatter.format_temp(f=60),
                            'summary': 'Cloudy'},
                            {'dayname': 'Tomorrow',
                            'max': formatter.format_temp(f=70),
                            'min': formatter.format_temp(f=55),
                            'summary': 'Light rain'}]}
        self.assertEqual(formatter.format_weather(data),
                         '\x02Narnia\x02 :: Sunny \x030780.0F/26.7C\x03 (Humidity: 80%) | '
                         '\x02Feels like:\x02 \x030785.0F/29.4C\x03 | '
                         '\x02Wind\x02: 12mph/19.3kph NNE | '
                         '\x02Wind gust\x02: 20mph/32.2kph | '
                         '\x02Today\x02: Cloudy. High \x0304100.0F/37.8C\x03. Low \x030360.0F/15.6C\x03. | '
                         '\x02Tomorrow\x02: Light rain. High \x030870.0F/21.1C\x03. Low \x030955.0F/12.8C\x03. | '
                         'Powered by \x02Dummy\x02 <http://dummy.invalid/api/>')
        #print(repr(formatter.format_weather(data)))

    def test_format_forecast(self):
        data = {'location': "Testville",
                'poweredby': 'Dummy',
                'url': 'http://dummy.invalid/api/',
                'current': {
                    'condition': 'Sunny',
                    'temperature': formatter.format_temp(f=80),
                    'feels_like': formatter.format_temp(f=85),
                    'humidity': formatter.format_percentage(0.8),
                    'precip': formatter.format_precip(mm=90),
                    'wind': formatter.format_distance(mi=12, speed=True),
                    'wind_gust': formatter.format_distance(mi=20, speed=True),
                    'wind_dir': formatter.wind_direction(15),
                    'uv': formatter.format_uv(6),
                    'visibility': formatter.format_distance(mi=1000),
                },
                'forecast': [{'dayname': 'Today',
                            'max': formatter.format_temp(f=100),
                            'min': formatter.format_temp(f=60),
                            'summary': 'Cloudy'},
                            {'dayname': 'Tomorrow',
                            'max': formatter.format_temp(f=70),
                            'min': formatter.format_temp(f=55),
                            'summary': 'Light rain'},
                            {'dayname': 'Tomorrow',
                            'max': formatter.format_temp(f=56),
                            'min': formatter.format_temp(f=40),
                            'summary': 'Heavy rain'}]}
        self.assertIn('\x02Testville\x02 :: \x02Today\x02: Cloudy (\x030360.0F/15.6C\x03 to \x0304100.0F/37.8C\x03) | '
                      '\x02Tomorrow\x02: Light rain (\x030955.0F/12.8C\x03 to \x030870.0F/21.1C\x03) | '
                      '\x02Tomorrow\x02: Heavy rain (\x030240.0F/4.4C\x03 to \x030956.0F/13.3C\x03)',
                      formatter.format_weather(data, True))
        #print(repr(formatter.format_weather(data, True)))

# FIXME: test geocode backends


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
