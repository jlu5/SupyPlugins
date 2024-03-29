###
# Copyright (c) 2018-2019, James Lu <james@overdrivenetworks.com>
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

from supybot import conf, registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NuWeather')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from .local import accountsdb

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('NuWeather', True)


NuWeather = conf.registerPlugin('NuWeather')
conf.registerGroup(NuWeather, 'apikeys')
conf.registerGroup(NuWeather, 'units')
conf.registerGlobalValue(NuWeather, accountsdb.CONFIG_OPTION_NAME, accountsdb.CONFIG_OPTION)

class NuWeatherTemperatureDisplayMode(registry.OnlySomeStrings):
    validStrings = ('F/C', 'C/F', 'F', 'C')

conf.registerChannelValue(NuWeather.units, 'temperature',
    NuWeatherTemperatureDisplayMode('F/C', _("""Determines how temperatures will be displayed.
        F/C means show "50F/10C", C means display only Celsius, and so on.""")))

class NuWeatherDistanceDisplayMode(registry.String):
    """Value must contain one of $mi, $km, or $m"""
    def setValue(self, v):
        if any(x in v for x in ('$mi', '$km', '$mi')):
            registry.String.setValue(self, v)
        else:
            self.error()

conf.registerChannelValue(NuWeather.units, 'distance',
    NuWeatherDistanceDisplayMode('$mi / $km', _("""Determines how distance values will be displayed.
        The following template variables are supported, and at least one must be included:
        $mi = miles, $km = kilometers, $m = meters.""")))
conf.registerChannelValue(NuWeather.units, 'speed',
    NuWeatherDistanceDisplayMode('$mi / $km', _("""Determines how speed values will be displayed.
        The following template variables are supported, and at least one must be included:
        $mi = mph, $km = km/h, $m = m/s.""")))

# List of supported backends for weather & geocode. This is reused by plugin.py
BACKENDS = ('openweathermap', 'pirateweather', 'weatherstack', 'wwis')
GEOCODE_BACKENDS = ('nominatim', 'googlemaps', 'opencage', 'weatherstack')

def backend_requires_apikey(backend):
    return backend not in ('wwis', 'nominatim')

class NuWeatherBackend(registry.OnlySomeStrings):
    validStrings = BACKENDS
class NuWeatherGeocode(registry.OnlySomeStrings):
    validStrings = GEOCODE_BACKENDS

conf.registerChannelValue(NuWeather, 'defaultBackend',
    NuWeatherBackend(BACKENDS[0], _("""Determines the default weather backend.""")))

conf.registerChannelValue(NuWeather, 'geocodeBackend',
    NuWeatherGeocode(GEOCODE_BACKENDS[0], _("""Determines the default geocode backend.""")))

for backend in BACKENDS + GEOCODE_BACKENDS:
    if backend_requires_apikey(backend):
        conf.registerGlobalValue(NuWeather.apikeys, backend,
            registry.String("", _("""Sets the API key for %s.""") % backend, private=True))

DEFAULT_FORMAT = ('\x02$location\x02 :: $c__condition $c__temperature '
                  '(Humidity: $c__humidity) | \x02Feels like:\x02 $c__feels_like '
                  '| \x02Wind\x02: $c__wind $c__wind_dir | \x02Wind gust\x02: $c__wind_gust '
                  '| \x02$f__0__dayname\x02: $f__0__summary. High $f__0__max. Low $f__0__min. '
                  '| \x02$f__1__dayname\x02: $f__1__summary. High $f__1__max. Low $f__1__min. '
                  '| Powered by \x02$poweredby\x02 $url')
conf.registerChannelValue(NuWeather, 'outputFormat',
    registry.String("", _("""EXPERIMENTAL: configures NuWeather's output format.
        Template names are not finalized and may change between releases. If in doubt, leave this
        option empty and the default format will be used: "%s\"""" % DEFAULT_FORMAT)))

DEFAULT_FORMAT_CURRENTONLY = ('\x02$location\x02 :: $c__condition $c__temperature '
                  '(Humidity: $c__humidity) | \x02Feels like:\x02 $c__feels_like '
                  '| \x02Wind\x02: $c__wind $c__wind_dir | \x02UV\x02: $c__uv '
                  '| \x02Visibility\x02: $c__visibility '
                  '| Powered by \x02$poweredby\x02 $url')
conf.registerChannelValue(NuWeather.outputFormat, 'currentOnly',
    registry.String("", _("""EXPERIMENTAL: configures NuWeather's output format when only current
        weather data is available.
        Template names are not finalized and may change between releases. If in doubt, leave this
        option empty and the default format will be used: "%s\"""" % DEFAULT_FORMAT_CURRENTONLY)))

forecastdays = []
for idx in range(5):  # Build up a 5 day forecast. XXX: not a user friendly config format
    forecastdays.append('\x02$f__{idx}__dayname\x02: $f__{idx}__summary ($f__{idx}__min to $f__{idx}__max)'.format(idx=idx))
DEFAULT_FORECAST_FORMAT = ('\x02$location\x02 :: %s | Powered by \x02$poweredby\x02 $url' % ' | '.join(forecastdays))

conf.registerChannelValue(NuWeather.outputFormat, 'forecast',
    registry.String("", _("""EXPERIMENTAL: configures NuWeather's output format for forecasts.
        Template names are not finalized and may change between releases. If in doubt, leave this
        option empty and the default format will be used: "%s\"""" % DEFAULT_FORECAST_FORMAT)))
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
