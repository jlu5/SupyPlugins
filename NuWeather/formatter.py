###
# Copyright (c) 2011-2014, Valentin Lorentz
# Copyright (c) 2018-2022, James Lu <james@overdrivenetworks.com>
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

import re
import string

from supybot import callbacks, conf, ircutils, log, utils

try:
    import pendulum
except ImportError:
    pendulum = None
    log.warning('NuWeather: pendulum is not installed; extended forecasts will not be formatted properly')

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NuWeather')
except ImportError:
    _ = lambda x: x

from .config import DEFAULT_FORMAT, DEFAULT_FORECAST_FORMAT, DEFAULT_FORMAT_CURRENTONLY

_channel_context = None
# dummy fallback for testing
_registryValue = lambda *args, **kwargs: ''

# Based off https://github.com/ProgVal/Supybot-plugins/blob/master/GitHub/plugin.py
def flatten_subdicts(dicts, flat=None):
    """Flattens a dict containing dicts or lists of dicts. Useful for string formatting."""
    if flat is None:
        # Instanciate the dictionnary when the function is run and now when it
        # is declared; otherwise the same dictionnary instance will be kept and
        # it will have side effects (memory exhaustion, ...)
        flat = {}
    if isinstance(dicts, list):
        return flatten_subdicts(dict(enumerate(dicts)))
    elif isinstance(dicts, dict):
        for key, value in dicts.items():
            if isinstance(value, dict):
                value = dict(flatten_subdicts(value))
                for subkey, subvalue in value.items():
                    flat['%s__%s' % (key, subkey)] = subvalue
            elif isinstance(value, list):
                for num, subvalue in enumerate(value):
                    if isinstance(subvalue, dict):
                        for subkey, subvalue in subvalue.items():
                            flat['%s__%s__%s' % (key, num, subkey)] = subvalue
                    else:
                        flat['%s__%s' % (key, num)] = subvalue
            else:
                flat[key] = value
        return flat
    else:
        return dicts

def format_temp(f=None, c=None):
    """
    Colorizes temperatures and formats them to show either Fahrenheit, Celsius, or both.
    """
    if f is None and c is None:
        return _('N/A')
    if f is None:
        f = c * 9/5 + 32
    elif c is None:
        c = (f - 32) * 5/9

    f = float(f)
    if f < 10:
        color = 'light blue'
    elif f < 32:
        color = 'teal'
    elif f < 50:
        color = 'blue'
    elif f < 60:
        color = 'light green'
    elif f < 70:
        color = 'green'
    elif f < 80:
        color = 'yellow'
    elif f < 90:
        color = 'orange'
    else:
        color = 'red'
    # Show temp values to one decimal place
    c = '%.1f' % c
    f = '%.1f' % f

    displaymode = _registryValue('units.temperature', channel=_channel_context)
    if displaymode == 'F/C':
        s = '%sF/%sC' % (f, c)
    elif displaymode == 'C/F':
        s = '%sC/%sF' % (c, f)
    elif displaymode == 'F':
        s = '%sF' % f
    elif displaymode == 'C':
        s = '%sC' % c
    else:
        raise ValueError("Unknown display mode for temperature.")
    return ircutils.mircColor(s, color)

_TEMPERATURES_RE = re.compile(r'((\d+)°?F)')  # Only need FtoC conversion so far
def mangle_temperatures(forecast):
    """Runs _format_temp() on temperature values embedded within forecast strings."""
    if not forecast:
        return forecast
    for (text, value) in set(_TEMPERATURES_RE.findall(forecast)):
        forecast = forecast.replace(text, format_temp(f=value))
    return forecast

def wind_direction(angle):
    """Returns wind direction (N, W, S, E, etc.) given an angle."""
    # Adapted from https://stackoverflow.com/a/7490772
    directions = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
    if angle is None:
        return directions[0] # dummy output
    angle = int(angle)
    idx = int((angle/(360/len(directions)))+.5)
    return directions[idx % len(directions)]

def format_uv(uv):
    """Formats UV levels with IRC colouring"""
    if uv is None:
        return _('N/A')
    # From https://en.wikipedia.org/wiki/Ultraviolet_index#Index_usage 2018-12-30
    uv = float(uv)
    if uv <= 2.9:
        color, risk = 'green', 'Low'
    elif uv <= 5.9:
        color, risk = 'yellow', 'Moderate'
    elif uv <= 7.9:
        color, risk = 'orange', 'High'
    elif uv <= 10.9:
        color, risk = 'red', 'Very high'
    else:
        # Closest we have to violet
        color, risk = 'pink', 'Extreme'
    s = '%d (%s)' % (uv, risk)
    return ircutils.mircColor(s, color)

def format_precip(mm=None, inches=None):
    """Formats precipitation to mm/in format"""
    if mm is None and inches is None:
        return _('N/A')
    elif mm == 0 or inches == 0:
        return '0'  # Don't bother with 2 units if the value is 0

    if mm is None:
        mm = round(inches * 25.4, 1)
    elif inches is None:
        inches = round(mm / 25.4, 1)

    return _('%smm/%sin') % (mm, inches)

def format_distance(mi=None, km=None, speed=False):
    """Formats distance or speed values in miles and kilometers"""
    if mi is None and km is None:
        return _('N/A')
    if mi == 0 or km == 0:
        return '0'  # Don't bother with multiple units if the value is 0

    if mi is None:
        mi = round(km / 1.609, 1)
    elif km is None:
        km = round(mi * 1.609, 1)

    if speed:
        m = f'{round(km / 3.6, 1)}m/s'
        mi = f'{mi}mph'
        km = f'{km}km/h'
        displaymode = _registryValue('units.speed', channel=_channel_context)
    else:
        m = f'{round(km * 1000, 1)}m'
        mi = f'{mi}mi'
        km = f'{km}km'
        displaymode = _registryValue('units.distance', channel=_channel_context)
    return string.Template(displaymode).safe_substitute(
        {'mi': mi, 'km': km, 'm': m}
    )

def format_percentage(value):
    """
    Formats percentage values given either as an int (value%) or float (0 <= value <= 1).
    """
    if isinstance(value, float):
        return '%.0f%%' % (value * 100)
    elif isinstance(value, int):
        return '%d%%' % value
    else:
        return 'N/A'

def get_dayname(ts, idx, *, tz=None):
    """
    Returns the day name given a Unix timestamp, day index and (optionally) a timezone.
    """
    if pendulum is not None:
        p = pendulum.from_timestamp(ts, tz=tz)
        return p.format('dddd')
    else:
        # Fallback
        if idx == 0:
            return 'Today'
        elif idx == 1:
            return 'Tomorrow'
        else:
            return 'Day_%d' % idx

def format_weather(data, forecast=False):
    """
    Formats and returns current conditions.
    """
    # Work around IRC length limits for config opts...
    data['c'] = data['current']
    data['f'] = data.get('forecast')

    flat_data = flatten_subdicts(data)
    if flat_data.get('url'):
        flat_data['url'] = utils.str.url(flat_data['url'])

    forecast_available = bool(data.get('forecast'))
    if forecast:  # --forecast option was given
        if forecast_available:
            fmt = _registryValue('outputFormat.forecast', channel=_channel_context) or DEFAULT_FORECAST_FORMAT
        else:
            raise callbacks.Error(_("Extended forecast info is not available from this backend."))
    else:
        if forecast_available:
            fmt = _registryValue('outputFormat', channel=_channel_context) or DEFAULT_FORMAT
        else:
            fmt = _registryValue('outputFormat.currentOnly', channel=_channel_context) or DEFAULT_FORMAT_CURRENTONLY
    template = string.Template(fmt)

    return template.safe_substitute(flat_data)
