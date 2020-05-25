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

from .config import BACKENDS, GEOCODE_BACKENDS, DEFAULT_FORMAT, DEFAULT_FORECAST_FORMAT, DEFAULT_FORMAT_CURRENTONLY
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
        if f is None:
            return _('N/A')

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

        url = 'https://nominatim.openstreetmap.org/search/%s?format=jsonv2' % utils.web.urlquote(location)
        self.log.debug('NuWeather: using url %s (geocoding)', url)
        # Custom User agent & caching are required for Nominatim per https://operations.osmfoundation.org/policies/nominatim/
        try:
            f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
            data = json.loads(f)
        except utils.web.Error as e:
            log.debug('NuWeather: error searching for %r from Nominatim backend:', location, exc_info=True)
            data = None
        if not data:
            raise callbacks.Error("Unknown location %r from OSM/Nominatim" % location)

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
        self.log.debug('NuWeather: saving %s,%s (osm_id %s, %s) for location %s from OSM/Nominatim', lat, lon, osm_id, display_name, location)

        result = (lat, lon, display_name, osm_id, "OSM/Nominatim")
        return result

    def _googlemaps_geocode(self, location):
        location = location.lower()
        apikey = self.registryValue('apikeys.googlemaps')
        if not apikey:
            raise callbacks.Error("No Google Maps API key.")

        url = "https://maps.googleapis.com/maps/api/geocode/json?address={0}&key={1}".format(utils.web.urlquote(location), apikey)
        self.log.debug('NuWeather: using url %s (geocoding)', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')

        data = json.loads(f)
        if data['status'] != "OK":
            raise callbacks.Error("{0} from Google Maps for location {1}".format(data['status'], location))

        data = data['results'][0]
        lat = data['geometry']['location']['lat']
        lon = data['geometry']['location']['lng']
        display_name = data['formatted_address']
        place_id = data['place_id']

        self.log.debug('NuWeather: saving %s,%s (place_id %s, %s) for location %s from Google Maps', lat, lon, place_id, display_name, location)
        result = (lat, lon, display_name, place_id, "Google\xa0Maps")
        return result

    def _opencage_geocode(self, location):
        location = location.lower()
        apikey = self.registryValue('apikeys.opencage')
        if not apikey:
            raise callbacks.Error("No OpenCage API key.")

        url = "https://api.opencagedata.com/geocode/v1/json?q={0}&key={1}&abbrv=1&limit=1".format(utils.web.urlquote(location), apikey)
        self.log.debug('NuWeather: using url %s (geocoding)', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')

        data = json.loads(f)
        if data['status']['message'] != "OK":
            raise callbacks.Error("{0} from OpenCage for location {1}".format(data['status']['message'], location))
        elif not data['results']:
            raise callbacks.Error("Unknown location %r from OpenCage" % location)

        data = data['results'][0]
        lat = data['geometry']['lat']
        lon = data['geometry']['lng']
        display_name = data['formatted']
        place_id = data['annotations']['geohash']

        self.log.debug('NuWeather: saving %s,%s (place_id %s, %s) for location %s from OpenCage', lat, lon, place_id, display_name, location)
        result = (lat, lon, display_name, place_id, "OpenCage")
        return result

    def _weatherstack_geocode(self, location):
        location = location.lower()
        apikey = self.registryValue('apikeys.weatherstack')
        if not apikey:
            raise callbacks.Error("No weatherstack API key.")

        url = "http://api.weatherstack.com/current?access_key={0}&query={1}".format(apikey, utils.web.urlquote(location))
        self.log.debug('NuWeather: using url %s (geocoding)', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')

        data = json.loads(f)
        if data.get('error'):
            raise callbacks.Error("{0} From weatherstack for location {1}".format(data['error']['info'], location))

        lat = data['location']['lat']
        lon = data['location']['lon']
        display_name = data['request']['query']
        place_id = "{0},{1}".format(lat, lon)

        self.log.debug('NuWeather: saving %s,%s (place_id %s,%s) for location %s from weatherstack', lat, lon, place_id, display_name, location)
        result = (lat, lon, display_name, place_id, "weatherstack")
        return result

    def _geocode(self, location, geobackend=None):
        geocode_backend = geobackend or self.registryValue('geocodeBackend', dynamic.msg.args[0])
        if geocode_backend not in GEOCODE_BACKENDS:
            raise callbacks.Error(_("Unknown geocode backend %r. Valid ones are: %s") % (geocode_backend, ', '.join(GEOCODE_BACKENDS)))

        result_pair = str((location, geocode_backend))  # escape for json purposes
        if result_pair in self.geocode_db:
            self.log.debug('NuWeather: using cached latlon %s for location %r', self.geocode_db[result_pair], location)
            return self.geocode_db[result_pair]
        elif location in self.geocode_db:
            # Old DBs from < 2019-03-14 only had one field storing location, and always
            # used OSM/Nominatim. Remove these old entries and regenerate them.
            self.log.debug('NuWeather: deleting outdated cached location %r', location)
            del self.geocode_db[location]

        backend_func = getattr(self, '_%s_geocode' % geocode_backend)
        result = backend_func(location)
        self.geocode_db[result_pair] = result  # Cache result persistently
        return result

    def _format(self, data, forecast=False):
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
                fmt = self.registryValue('outputFormat.forecast', dynamic.msg.args[0]) or DEFAULT_FORECAST_FORMAT
            else:
                raise callbacks.Error(_("Extended forecast info is not available from this backend."))
        else:
            if forecast_available:
                fmt = self.registryValue('outputFormat', dynamic.msg.args[0]) or DEFAULT_FORMAT
            else:
                fmt = self.registryValue('outputFormat.currentOnly', dynamic.msg.args[0]) or DEFAULT_FORMAT_CURRENTONLY
        template = string.Template(fmt)

        return template.safe_substitute(flat_data)

    def _weatherstack_fetcher(self, location, geobackend=None):
        """Grabs weather data from weatherstack (formerly Apixu)."""
        apikey = self.registryValue('apikeys.weatherstack')
        if not apikey:
            raise callbacks.Error(_("Please configure the weatherstack API key in plugins.nuweather.apikeys.weatherstack . "
                                    "Apixu users please see https://github.com/apilayer/weatherstack#readme"))
        # HTTPS is not supported on free accounts. Don't ask me why
        url = 'http://api.weatherstack.com/current?' + utils.web.urlencode({
            'access_key': apikey,
            'query': location,
            'units': 'f',
        })
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f)

        currentdata = data['current']

        return {
            'location': data['request']['query'],
            'poweredby': 'weatherstack',
            'url': '',
            'current': {
                'condition': currentdata['weather_descriptions'][0],
                'temperature': self._format_temp(f=currentdata['temperature']),
                'feels_like': self._format_temp(f=currentdata['feelslike']),
                'humidity': self._format_percentage(currentdata['humidity']),
                'precip': self._format_precip(inches=currentdata['precip']),
                'wind': self._format_distance(mi=currentdata['wind_speed'], speed=True),
                'wind_dir': currentdata['wind_dir'],
                'uv': self._format_uv(currentdata['uv_index']),
                'visibility': self._format_distance(mi=currentdata.get('visibility')),
            }
        }

    def _darksky_fetcher(self, location, geobackend=None):
        """Grabs weather data from Dark Sky."""
        apikey = self.registryValue('apikeys.darksky')
        if not apikey:
            raise callbacks.Error(_("Please configure the Dark Sky API key in plugins.nuweather.apikeys.darksky."))

        # Convert location to lat,lon first
        latlon = self._geocode(location, geobackend=geobackend)
        if not latlon:
            raise callbacks.Error("Unknown location %s." % location)

        lat, lon, display_name, geocodeid, geocode_backend = latlon

        # We don't use minutely or hourly data; alerts are not supported yet
        url = 'https://api.darksky.net/forecast/%s/%s,%s?units=us&exclude=minutely,hourly,alerts' % (apikey, lat, lon)
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f, strict=False)

        currentdata = data['currently']

        # N.B. Dark Sky docs tell to not expect any values to exist except the timestamp attached to the response
        return {
            'location': display_name,
            'poweredby': 'Dark\xa0Sky+' + geocode_backend,
            'url': 'https://darksky.net/forecast/%s,%s' % (lat, lon),
            'current': {
                'condition': currentdata.get('summary', 'N/A'),
                'temperature': self._format_temp(f=currentdata.get('temperature')),
                'feels_like': self._format_temp(f=currentdata.get('apparentTemperature')),
                'humidity': self._format_percentage(currentdata.get('humidity')),
                'precip': self._format_precip(mm=currentdata.get('precipIntensity')),
                'wind': self._format_distance(mi=currentdata.get('windSpeed', 0), speed=True),
                'wind_gust': self._format_distance(mi=currentdata.get('windGust', 0), speed=True),
                'wind_dir': self._wind_direction(currentdata.get('windBearing')),
                'uv': self._format_uv(currentdata.get('uvIndex')),
                'visibility': self._format_distance(mi=currentdata.get('visibility')),
            },
            'forecast': [{'dayname': self._get_dayname(forecastdata['time'], idx, tz=data['timezone']),
                          'max': self._format_temp(f=forecastdata.get('temperatureHigh')),
                          'min': self._format_temp(f=forecastdata.get('temperatureLow')),
                          'summary': forecastdata.get('summary', 'N/A').rstrip('.')} for idx, forecastdata in enumerate(data['daily']['data'])]
        }

    def _openweathermap_fetcher(self, location, geobackend=None):
        """Grabs weather data from OpenWeatherMap."""
        apikey = self.registryValue('apikeys.openweathermap')
        if not apikey:
            raise callbacks.Error(_("Please configure the OpenWeatherMap API key in plugins.nuweather.apikeys.openweathermap"))

        # Convert location to lat,lon first
        latlon = self._geocode(location, geobackend=geobackend)
        if not latlon:
            raise callbacks.Error("Unknown location %s." % location)

        lat, lon, __, ___, geocode_backend = latlon
        url = 'https://api.openweathermap.org/data/2.5/weather?' + utils.web.urlencode({
            'appid': apikey,
            'lat': lat,
            'lon': lon,
            'units': 'imperial',
        })
        self.log.debug('NuWeather: using url %s (current data)', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f, strict=False)

        output = {
            'location': '%s, %s' % (data['name'], data['sys']['country']),
            'poweredby': 'OpenWeatherMap+' + geocode_backend,
            'url': 'https://openweathermap.org/weathermap?' + utils.web.urlencode({
                'lat': lat,
                'lon': lon,
                'zoom': 12
            }),
            # Unfortunately not all of the fields we use are available
            'current': {
                'condition': data['weather'][0]['description'],
                'temperature': self._format_temp(f=data['main']['temp']),
                'feels_like': 'N/A',
                'humidity': self._format_percentage(data['main']['humidity']),
                'precip': 'N/A',
                'wind': self._format_distance(mi=data['wind']['speed'], speed=True),
                'wind_gust': 'N/A',
                'wind_dir': self._wind_direction(data['wind']['deg']),
                'uv': 'N/A',  # Requires a separate API call
                'visibility': self._format_distance(km=data['visibility']/1000),
            }
        }
        tzoffset = data['timezone']

        # Get extended forecast (a separate API call)
        url = 'https://api.openweathermap.org/data/2.5/forecast?' + utils.web.urlencode({
            'appid': apikey,
            'lat': lat,
            'lon': lon,
            'units': 'imperial',
        })
        self.log.debug('NuWeather: using url %s (extended forecast)', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f, strict=False)
        def _owm_make_dayname(utcts):
            # OWM gives timestamps in UTC, but the /weather endpoint provides a timezone
            # offset in seconds. Use this data with pendulum to generate a human readable time.
            ts = utcts + tzoffset

            if pendulum:
                dt = pendulum.from_timestamp(ts)
                return dt.format('dddd hA')  # Return strings like "Sunday 8PM"
            return ts  # fallback

        # OWM's 5 day forecast gives data by 3 hour intervals. The actual daily forecast
        # requires a subscription.
        output['forecast'] = [
            {'dayname': _owm_make_dayname(forecast['dt']),
             'max': self._format_temp(f=forecast['main']['temp_max']),
             'min': self._format_temp(f=forecast['main']['temp_min']),
             'summary': forecast['weather'][0]['description']}
            for forecast in data['list'][1::2]  # grab data every 6 hours, excluding first pocket
        ]
        return output

    @wrap([getopts({'user': 'nick', 'backend': None, 'weather-backend': None, 'geocode-backend': None, 'forecast': ''}), additional('text')])
    def weather(self, irc, msg, args, optlist, location):
        """[--user <othernick>] [--weather-backend/--backend <weather backend>] [--geocode-backend <geocode backend>] [--forecast] [<location>]

        Fetches weather and forecast information for <location>. <location> can be left blank if you have a previously set location (via 'setweather').

        If --forecast is specified, show an extended (default: 5-day) forecast for <location>.

        If the --user option is specified, show weather for the saved location of that nick, instead of the caller's.

        If either --weather-backend/--backend or --geocode-backend is specified, will override the default backends if provided backend is available.
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

        weather_backend = optlist.get('weather-backend') or optlist.get('backend') or self.registryValue('defaultBackend', msg.args[0])
        if weather_backend not in BACKENDS:
            irc.error(_("Unknown weather backend %s. Valid ones are: %s") % (weather_backend, ', '.join(BACKENDS)), Raise=True)
        geocode_backend = optlist.get('geocode-backend', self.registryValue('geocodeBackend', msg.args[0]))

        backend_func = getattr(self, '_%s_fetcher' % weather_backend)
        raw_data = backend_func(location, geocode_backend)

        s = self._format(raw_data, forecast='forecast' in optlist)
        irc.reply(s)

    @wrap([getopts({'user': 'nick', 'backend': None}), 'text'])
    def geolookup(self, irc, msg, args, optlist, location):
        """[--backend <backend>] <location>

        Looks up <location> using a geocoding backend.
        """
        optlist = dict(optlist)
        geocode_backend = optlist.get('backend', self.registryValue('geocodeBackend', msg.args[0]))

        data = self._geocode(location, geobackend=geocode_backend)
        lat, lon, display_name, place_id, backend = data

        s = 'From %s: \x02%s\x02 [ID: %s] \x02%s,%s' % (backend, display_name, place_id, lat, lon)
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
