###
# Copyright (c) 2019-2022, James Lu <james@overdrivenetworks.com>
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

from .config import BACKENDS, backend_requires_apikey

NO_NETWORK_REASON = "Network-based tests are disabled by --no-network"
class NuWeatherTestCase(PluginTestCase):
    plugins = ('NuWeather',)

    # These tests are not meant to be exhaustive, since I don't want to hit my free tier
    # API limits :(

    @staticmethod
    def _set_backend(backend):
        if backend_requires_apikey(backend):
            varname = 'NUWEATHER_APIKEY_%s' % backend.upper()
            apikey = os.environ.get(varname)
            if apikey:
                log.info('NuWeather: Set API key for %s from env var %s', backend, varname)
                conf.supybot.plugins.NuWeather.apikeys.get(backend).setValue(apikey)
            else:
                raise RuntimeError(f"Please set the {varname} environment variable to run this test")

        # Update default backend
        conf.supybot.plugins.NuWeather.defaultbackend.setValue(backend)

    @unittest.skipUnless(network, NO_NETWORK_REASON)
    def testWeather(self):
        for backend in BACKENDS:
            with self.subTest(msg=f"{backend} backend"):
                self._set_backend(backend)
                self.assertRegexp('weather Vancouver', 'Vancouver,')
                self.assertRegexp('weather LAX', 'Los Angeles')
                #self.assertRegexp('weather 76010', 'Arlington')  # US ZIP codes not supported by Nominatim (default)

    @unittest.skipUnless(network, NO_NETWORK_REASON)
    def testSavedLocation(self):
        self._set_backend(BACKENDS[0])
        self.assertError('weather')  # No location set
        self.assertNotError('setweather Berlin')
        self.assertRegexp('weather', 'Berlin')

# TODO: test geolookup code, using the separate command

from . import formatter

class NuWeatherFormatterTestCase(PluginTestCase):
    plugins = ('NuWeather',)
    maxDiff = None

    def setUp(self, nick='test', forceSetup=True):
        super().setUp(nick=nick, forceSetup=forceSetup)
        cb = self.irc.getCallback('NuWeather')

        # These helpers pull the display template from Limnoria config
        self._format_temp = cb._format_tmpl_temp
        self._format_distance = cb._format_tmpl_distance
        self._format_speed = lambda *args, **kwargs: self._format_distance(*args, speed=True, **kwargs)
        self._format_weather = cb._format_weather

    def test_format_temp(self):
        func = self._format_temp
        self.assertEqual(func(f=50, c=10), '\x031150.0F/10.0C\x03')
        self.assertEqual(func(f=100), '\x0307100.0F/37.8C\x03')
        self.assertEqual(func(c=25.55), '\x030878.0F/25.6C\x03')
        self.assertEqual(func(), 'N/A')

    def test_format_temp_displaymode(self):
        func = self._format_temp
        with conf.supybot.plugins.NuWeather.units.temperature.context('F/C'):
            self.assertEqual(func(c=-5.3), '\x031222.5F/-5.3C\x03')
        with conf.supybot.plugins.NuWeather.units.temperature.context('C/F'):
            self.assertEqual(func(f=50, c=10), '\x031110.0C/50.0F\x03')
        with conf.supybot.plugins.NuWeather.units.temperature.context('C'):
            self.assertEqual(func(c=36), '\x030736.0C\x03')
        with conf.supybot.plugins.NuWeather.units.temperature.context('F'):
            self.assertEqual(func(f=72), '\x030972.0F\x03')

    def test_format_distance(self):
        func = self._format_distance
        self.assertEqual(func(mi=123), '123mi / 197.9km')
        self.assertEqual(func(km=42.6), '26.5mi / 42.6km')
        self.assertEqual(func(mi=26, km=42), '26mi / 42km')
        self.assertEqual(func(mi=0), '0')  # special case
        self.assertEqual(func(), 'N/A')

    def test_format_distance_speed(self):
        func = self._format_speed
        self.assertEqual(func(mi=123), '123mph / 197.9km/h')
        self.assertEqual(func(km=42.6), '26.5mph / 42.6km/h')
        self.assertEqual(func(mi=26, km=42), '26mph / 42km/h')
        self.assertEqual(func(mi=0), '0')  # special case
        self.assertEqual(func(), 'N/A')

    def test_format_distance_displaymode(self):
        func = self._format_distance
        with conf.supybot.plugins.NuWeather.units.distance.context('$mi / $km / $m'):
            self.assertEqual(func(mi=123), '123mi / 197.9km / 197949.3m')
            self.assertEqual(func(km=42.6), '26.5mi / 42.6km / 42600.0m')
        with conf.supybot.plugins.NuWeather.units.distance.context('$m/$km'):
            self.assertEqual(func(km=2), '2000m/2km')

    def test_format_distance_speed_displaymode(self):
        func = self._format_speed
        with conf.supybot.plugins.NuWeather.units.speed.context('$mi / $km / $m'):
            self.assertEqual(func(mi=123), '123mph / 197.9km/h / 55.0m/s')
        with conf.supybot.plugins.NuWeather.units.speed.context('$m / $km'):
            self.assertEqual(func(km=2), '0.6m/s / 2km/h')

    def test_format_default(self):
        data = {'location': "Narnia",
                'poweredby': 'Dummy',
                'url': 'http://dummy.invalid/api/',
                'current': {
                    'condition': 'Sunny',
                    'temperature': self._format_temp(f=80),
                    'feels_like': self._format_temp(f=85),
                    'humidity': formatter.format_percentage(0.8),
                    'precip': formatter.format_precip(mm=90),
                    'wind': self._format_distance(mi=12, speed=True),
                    'wind_gust': self._format_distance(mi=20, speed=True),
                    'wind_dir': formatter.wind_direction(15),
                    'uv': formatter.format_uv(6),
                    'visibility': self._format_distance(mi=1000),
                },
                'forecast': [{'dayname': 'Today',
                            'max': self._format_temp(f=100),
                            'min': self._format_temp(f=60),
                            'summary': 'Cloudy'},
                            {'dayname': 'Tomorrow',
                            'max': self._format_temp(f=70),
                            'min': self._format_temp(f=55),
                            'summary': 'Light rain'}]}
        output = self._format_weather(data, None, False)
        #print(repr(output))
        self.assertEqual(output,
                         '\x02Narnia\x02 :: Sunny \x030880.0F/26.7C\x03 (Humidity: 80%) '
                         '| \x02Feels like:\x02 \x030885.0F/29.4C\x03 | \x02Wind\x02: 12mph / 19.3km/h NNE '
                         '| \x02Wind gust\x02: 20mph / 32.2km/h | \x02Today\x02: Cloudy. High \x0307100.0F/37.8C\x03. '
                         'Low \x031160.0F/15.6C\x03. | \x02Tomorrow\x02: Light rain. High \x030970.0F/21.1C\x03. '
                         'Low \x031155.0F/12.8C\x03. | Powered by \x02Dummy\x02 <http://dummy.invalid/api/>')

    def test_format_forecast(self):
        data = {'location': "Testville",
                'poweredby': 'Dummy',
                'url': 'http://dummy.invalid/api/',
                'current': {
                    'condition': 'Sunny',
                    'temperature': self._format_temp(f=80),
                    'feels_like': self._format_temp(f=85),
                    'humidity': formatter.format_percentage(0.8),
                    'precip': formatter.format_precip(mm=90),
                    'wind': self._format_distance(mi=12, speed=True),
                    'wind_gust': self._format_distance(mi=20, speed=True),
                    'wind_dir': formatter.wind_direction(15),
                    'uv': formatter.format_uv(6),
                    'visibility': self._format_distance(mi=1000),
                },
                'forecast': [{'dayname': 'Today',
                            'max': self._format_temp(f=100),
                            'min': self._format_temp(f=60),
                            'summary': 'Cloudy'},
                            {'dayname': 'Tomorrow',
                            'max': self._format_temp(f=70),
                            'min': self._format_temp(f=55),
                            'summary': 'Light rain'},
                            {'dayname': 'Tomorrow',
                            'max': self._format_temp(f=56),
                            'min': self._format_temp(f=40),
                            'summary': 'Heavy rain'}]}
        self.assertIn('\x02Testville\x02 :: \x02Today\x02: Cloudy (\x031160.0F/15.6C\x03 to \x0307100.0F/37.8C\x03) | \x02Tomorrow\x02: Light rain (\x031155.0F/12.8C\x03 to \x030970.0F/21.1C\x03) | ',
                      self._format_weather(data, None, True))
        #print(repr(self._format_weather(data, None, True)))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=120:
