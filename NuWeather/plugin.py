###
# Copyright (c) 2011-2014, Valentin Lorentz
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
import json
import os
import re
import string

from supybot import utils, plugins, ircutils, callbacks, world, conf, log
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NuWeather')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

try:
    import pendulum
except ImportError:
    pendulum = None
    log.warning('NuWeather: pendulum is not installed; extended forecasts will not be formatted properly')

from .config import BACKENDS, DEFAULT_FORMAT, DEFAULT_FORECAST_FORMAT
from .local import accountsdb

HEADERS = {
    'User-agent': 'Mozilla/5.0 (compatible; Supybot/Limnoria %s; NuWeather weather plugin)' % conf.version
}

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

class NuWeather(callbacks.Plugin):
    """Weather plugin for Limnoria"""
    threaded = True

    def __init__(self, irc):
        super().__init__(irc)
        # We use 2 DBs: one to store preferred locations and another for location latlon (geocoding)
        self.db = accountsdb.AccountsDB("NuWeather", 'NuWeather.db', self.registryValue(accountsdb.CONFIG_OPTION_NAME))
        geocode_db_filename = conf.supybot.directories.data.dirize("NuWeather-geocode.json")
        if os.path.exists(geocode_db_filename):
            with open(geocode_db_filename) as f:
                self.geocode_db = json.load(f)
        else:
            self.log.info("NuWeather: Creating new geocode DB")
            self.geocode_db = {}
        world.flushers.append(self.db.flush)
        world.flushers.append(self._flush_geocode_db)

    def _flush_geocode_db(self):
        geocode_db_filename = conf.supybot.directories.data.dirize("NuWeather-geocode.json")
        with open(geocode_db_filename, 'w') as f:
            json.dump(self.geocode_db, f)

    def die(self):
        world.flushers.remove(self.db.flush)
        world.flushers.remove(self._flush_geocode_db)
        self.db.flush()
        self._flush_geocode_db()
        super().die()

    def _format_temp(self, f, c=None):
        """
        Colorizes temperatures and formats them to show either Fahrenheit, Celsius, or both.
        """
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
        # Round to nearest tenth for display purposes
        if c is None:
            c = round((f - 32) * 5/9, 1)
        else:
            c = round(c, 1)
        f = round(f, 1)

        displaymode = self.registryValue('units.temperature', dynamic.msg.args[0])
        if displaymode == 'F/C':
            string = '%sF/%sC' % (f, c)
        elif displaymode == 'C/F':
            string = '%sC/%sF' % (c, f)
        elif displaymode == 'F':
            string = '%sF' % f
        elif displaymode == 'C':
            string = '%sC' % c
        else:
            raise ValueError("Unknown display mode for temperature.")
        return ircutils.mircColor(string, color)

    _temperatures_re = re.compile(r'((\d+)°?F)')  # Only need FtoC conversion so far
    def _mangle_temperatures(self, forecast):
        """Runs _format_temp() on temperature values embedded within forecast strings."""
        if not forecast:
            return forecast
        for (text, value) in set(self._temperatures_re.findall(forecast)):
            forecast = forecast.replace(text, self._format_temp(f=value))
        return forecast

    @staticmethod
    def _wind_direction(angle):
        """Returns wind direction (N, W, S, E, etc.) given an angle."""
        # Adapted from https://stackoverflow.com/a/7490772
        directions = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
        if angle is None:
            return directions[0] # dummy output
        angle = int(angle)
        idx = int((angle/(360/len(directions)))+.5)
        return directions[idx % len(directions)]

    @staticmethod
    def _format_uv(uv):
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
        string = '%d (%s)' % (uv, risk)
        return ircutils.mircColor(string, color)

    @staticmethod
    def _format_precip(mm=None, inches=None):
        if mm is None and inches is None:
            return _('N/A')
        elif mm == 0 or inches == 0:
            return '0'  # Don't bother with 2 units if the value is 0

        if mm is None:
            mm = round(inches * 25.4, 1)
        elif inches is None:
            inches = round(mm / 25.4, 1)

        return _('%smm/%sin') % (mm, inches)

    @staticmethod
    def _format_distance(mi=None, km=None, speed=False):
        if mi is None and km is None:
            return _('N/A')
        elif mi == 0 or km == 0:
            return '0'  # Don't bother with 2 units if the value is 0

        if mi is None:
            mi = round(km / 1.609, 1)
        elif km is None:
            km = round(mi * 1.609, 1)

        if speed:
            return _('%smph/%skph') % (mi, km)
        else:
            return _('%smi/%skm') % (mi, km)

    @staticmethod
    def _format_percentage(value):
        """
        Formats percentage values given either as an int (value%) or float (0 <= value <= 1).
        """
        if isinstance(value, float):
            return '%.0f%%' % (value * 100)
        elif isinstance(value, int):
            return '%d%%' % value
        else:
            return 'N/A'

    @staticmethod
    def _get_dayname(ts, idx, *, tz=None):
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

    def _nominatim_geocode(self, location):
        location = location.lower()
        if location in self.geocode_db:
            self.log.debug('NuWeather: using cached latlon %s for location %s', self.geocode_db[location], location)
            return self.geocode_db[location]

        url = 'https://nominatim.openstreetmap.org/search/%s?format=jsonv2' % utils.web.urlquote(location)
        self.log.debug('NuWeather: using url %s (geocoding)', url)
        # Custom User agent & caching are required for Nominatim per https://operations.osmfoundation.org/policies/nominatim/
        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f)
        if not data:
            raise callbacks.Error("Unknown location %s." % location)

        data = data[0]
        # Limit location verbosity to 3 divisions (e.g. City, Province/State, Country)
        display_name = data['display_name']
        display_name_parts = display_name.split(', ')
        if len(display_name_parts) > 3:
            if display_name_parts[-2].isdigit():  # Try to remove ZIP code-like divisions
                display_name_parts.pop(-2)
            display_name = ', '.join([display_name_parts[0]] + display_name_parts[-2:])

        lat = data['lat']
        lon = data['lon']
        osm_id = data.get('osm_id')
        self.log.debug('NuWeather: saving %s,%s (osm_id %s, %s) for location %s', lat, lon, osm_id, display_name, location)

        result = (lat, lon, display_name, osm_id)
        self.geocode_db[location] = result  # Cache result persistently
        return result

    _geocode = _nominatim_geocode  # Maybe we'll add more backends for this in the future?
    _geocode.backend = "OSM/Nominatim"

    def _format(self, data, forecast=False):
        """
        Formats and returns current conditions.
        """
        # Work around IRC length limits for config opts...
        data['c'] = data['current']
        data['f'] = data['forecast']

        flat_data = flatten_subdicts(data)
        if flat_data.get('url'):
            flat_data['url'] = utils.str.url(flat_data['url'])

        if forecast:
            fmt = self.registryValue('outputFormat.forecast', dynamic.msg.args[0]) or DEFAULT_FORECAST_FORMAT
        else:
            fmt = self.registryValue('outputFormat', dynamic.msg.args[0]) or DEFAULT_FORMAT
        template = string.Template(fmt)

        return template.safe_substitute(flat_data)

    def _apixu_fetcher(self, location):
        """Grabs weather data from Apixu."""
        apikey = self.registryValue('apikeys.apixu')
        if not apikey:
            raise callbacks.Error(_("Please configure the apixu API key in plugins.nuweather.apikeys.apixu."))
        url = 'https://api.apixu.com/v1/forecast.json?' + utils.web.urlencode({
            'key': apikey,
            'q': location,
            'days': 5
        })
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f)

        locationdata = data['location']
        if locationdata['region']:
            location = "%s, %s, %s" % (locationdata['name'], locationdata['region'], locationdata['country'])
        else:
            location = "%s, %s" % (locationdata['name'], locationdata['country'])

        currentdata = data['current']

        return {
            'location': location,
            'poweredby': 'Apixu',
            'url': '',
            'current': {
                'condition': currentdata['condition']['text'],
                'temperature': self._format_temp(currentdata['temp_f'], currentdata['temp_c']),
                'feels_like': self._format_temp(currentdata['feelslike_f'], currentdata['feelslike_c']),
                'humidity': self._format_percentage(currentdata['humidity']),
                'precip': self._format_precip(currentdata['precip_mm'], currentdata['precip_in']),
                'wind': self._format_distance(currentdata['wind_mph'], currentdata['wind_kph'], speed=True),
                'wind_dir': currentdata['wind_dir'],
                'uv': self._format_uv(currentdata['uv']),
                'visibility': self._format_distance(currentdata.get('vis_miles'), currentdata.get('vis_km')),
            },
            'forecast': [{'dayname': self._get_dayname(forecastdata['date_epoch'], idx, tz=locationdata['tz_id']),
                          'max': self._format_temp(forecastdata['day']['maxtemp_f'], forecastdata['day']['maxtemp_c']),
                          'min': self._format_temp(forecastdata['day']['mintemp_f'], forecastdata['day']['mintemp_c']),
                          'summary': forecastdata['day']['condition']['text']} for idx, forecastdata in enumerate(data['forecast']['forecastday'])]
        }

    def _darksky_fetcher(self, location):
        """Grabs weather data from Dark Sky."""
        apikey = self.registryValue('apikeys.darksky')
        if not apikey:
            raise callbacks.Error(_("Please configure the Dark Sky API key in plugins.nuweather.apikeys.darksky."))

        # Convert location to lat,lon first
        latlon = self._geocode(location)
        if not latlon:
            raise callbacks.Error("Unknown location %s." % location)

        lat, lon, display_name, geocodeid = latlon

        # Request US units - this is reflected (mi, mph) and processed in our output format as needed
        url = 'https://api.darksky.net/forecast/%s/%s,%s?units=us&exclude=minutely' % (apikey, lat, lon)
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f, strict=False)

        currentdata = data['currently']

        # N.B. Dark Sky docs tell to not expect any values to exist except the timestamp attached to the response
        return {
            'location': display_name,
            'poweredby': 'Dark\xa0Sky+' + self._geocode.backend,
            'url': 'https://darksky.net/forecast/%s,%s' % (lat, lon),
            'current': {
                'condition': currentdata.get('summary', 'N/A'),
                'temperature': self._format_temp(f=currentdata.get('temperature')),
                'feels_like': self._format_temp(f=currentdata.get('apparentTemperature')),
                'humidity': self._format_percentage(currentdata.get('humidity')),
                'precip': self._format_precip(mm=currentdata.get('precipIntensity')),
                'wind': self._format_distance(mi=currentdata.get('windSpeed', 0), speed=True),
                'wind_dir': self._wind_direction(currentdata.get('windBearing')),
                'uv': self._format_uv(currentdata.get('uvIndex')),
                'visibility': self._format_distance(mi=currentdata['visibility']),
            },
            'forecast': [{'dayname': self._get_dayname(forecastdata['time'], idx, tz=data['timezone']),
                          'max': self._format_temp(f=forecastdata['temperatureHigh']),
                          'min': self._format_temp(f=forecastdata['temperatureLow']),
                          'summary': forecastdata['summary'].rstrip('.')} for idx, forecastdata in enumerate(data['daily']['data'])]
        }

    @wrap([getopts({'user': 'nick', 'backend': None, 'forecast': ''}), additional('text')])
    def weather(self, irc, msg, args, optlist, location):
        """[--user <othernick>] [--backend <backend>] [--forecast] [<location>]

        Fetches weather and forecast information for <location>. <location> can be left blank if you have a previously set location (via 'setweather').

        If --forecast is specified, show an extended (default: 5-day) forecast for <location>.

        If the --user option is specified, show weather for the saved location of that nick, instead of the caller's.
        """
        optlist = dict(optlist)
        # Default to the caller
        if optlist.get('user'):
            try:
                hostmask = irc.state.nickToHostmask(optlist['user'])
            except KeyError:
                irc.error(_("I don't know who %r is.") % optlist['user'], Raise=True)
        else:
            hostmask = msg.prefix
        # Can be specified location or default one in DB
        location = location or self.db.get(hostmask)

        if not location:
            irc.error(_("I did not find a preset location for you. Please set one via 'setweather <location>'."), Raise=True)

        backend = optlist.get('backend', self.registryValue('defaultBackend', msg.args[0]))
        if backend not in BACKENDS:
            irc.error(_("Unknown weather backend %s. Valid ones are: %s") % (backend, ', '.join(BACKENDS)), Raise=True)

        backend_func = getattr(self, '_%s_fetcher' % backend)
        raw_data = backend_func(location)

        s = self._format(raw_data, forecast='forecast' in optlist)
        irc.reply(s)

    @wrap(['text'])
    def setweather(self, irc, msg, args, location):
        """<location>

        Saves the weather location for your bot account, or hostmask if you are not registered.
        """
        self.db.set(msg.prefix, location)
        irc.replySuccess()

Class = NuWeather


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
