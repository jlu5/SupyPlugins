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
import string

from supybot import ircutils, log

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

def format_temp(displaymode, f=None, c=None):
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
    # Roughly inspired by https://www.esri.com/arcgis-blog/products/arcgis-pro/mapping/a-meaningful-temperature-palette/
    if f > 100:
        color = '4'  # red
    elif f > 85:
        color = '7'  # orange
    elif f > 75:
        color = '8'  # yellow
    elif f > 60:
        color = '9'  # light green
    elif f > 40:
        color = '11' # cyan
    elif f > 10:
        color = '12' # light blue
    else:
        color = '15' # light grey

    # Show temp values to one decimal place
    c = '%.1f' % c
    f = '%.1f' % f

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
    return f'\x03{color.zfill(2)}{s}\x03'

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

def format_distance(displaymode, mi=None, km=None, speed=False):
    """Formats distance or speed values in miles and kilometers"""
    if mi is None and km is None:
        return _('N/A')
    if mi == 0 or km == 0:
        return '0'  # Don't bother with multiple units if the value is 0

    if mi is None:
        mi = km / 1.609344
    elif km is None:
        km = mi * 1.609344

    if speed:
        m = f'{round(km / 3.6, 1)}m/s'
        mi = f'{round(mi, 1)}mph'
        km = f'{round(km, 1)}km/h'
    else:
        m = f'{round(km * 1000, 1)}m'
        mi = f'{round(mi, 1)}mi'
        km = f'{round(km, 1)}km'
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

def get_dayname(ts, idx, *, tz=None, fallback=None):
    """
    Returns the day name given a Unix timestamp, day index and (optionally) a timezone.
    """
    if pendulum is not None:
        p = pendulum.from_timestamp(ts, tz=tz)
        return p.format('dddd')
    else:
        if fallback:
            return fallback
        # Fallback
        if idx == 0:
            return 'Today'
        elif idx == 1:
            return 'Tomorrow'
        else:
            return 'Day_%d' % idx


