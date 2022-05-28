###
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
import json
import os
import time

from supybot import utils, plugins, ircutils, callbacks, world, conf, log
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NuWeather')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from .config import BACKENDS, GEOCODE_BACKENDS
from .local import accountsdb
from . import formatter

HEADERS = {
    'User-agent': 'Mozilla/5.0 (compatible; Supybot/Limnoria %s; NuWeather weather plugin)' % conf.version
}

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
        # this is hacky but less annoying than navigating the registry ourselves
        formatter._registryValue = self.registryValue

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

        lat = float(data['lat'])
        lon = float(data['lon'])
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
        geocode_backend = geobackend or self.registryValue('geocodeBackend', channel=formatter._channel_context)
        if geocode_backend not in GEOCODE_BACKENDS:
            raise callbacks.Error(_("Unknown geocode backend %r. Valid ones are: %s") % (geocode_backend, ', '.join(GEOCODE_BACKENDS)))

        result_pair = str((location, geocode_backend))  # escape for json purposes
        if result_pair in self.geocode_db:
            # 2022-05-24: fix Nominatim returning the wrong type
            if not isinstance(result_pair[0], float):
                del self.geocode_db[result_pair]
            else:
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
                'temperature': formatter.format_temp(f=currentdata['temperature']),
                'feels_like': formatter.format_temp(f=currentdata['feelslike']),
                'humidity': formatter.format_percentage(currentdata['humidity']),
                'precip': formatter.format_precip(inches=currentdata['precip']),
                'wind': formatter.format_distance(mi=currentdata['wind_speed'], speed=True),
                'wind_dir': currentdata['wind_dir'],
                'uv': formatter.format_uv(currentdata['uv_index']),
                'visibility': formatter.format_distance(mi=currentdata.get('visibility')),
            }
        }

    def _load_check_time(self, url, cache_path, desc, cache_ttl):
        if not os.path.exists(cache_path) or \
                (time.time() - os.path.getmtime(cache_path)) > cache_ttl:
            log.debug(f'NuWeather: refreshing {desc} from {url}')
            data_text = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
            with open(cache_path, 'w', encoding='utf-8') as f:
                log.debug(f'NuWeather: saving {desc} to {cache_path}')
                f.write(data_text)
            data = json.loads(data_text)
            self._wwis_cities.clear()
        else:
            with open(cache_path, encoding='utf-8') as f:
                log.debug(f'NuWeather: reloading existing {desc} from {cache_path}')
                data = json.load(f)
        return data

    _WWIS_CITIES_REFRESH_INTERVAL = 2592000  # 30 days
    _wwis_cities = {}
    def _wwis_load_cities(self, lang='en'):
        wwis_cache_path = conf.supybot.directories.data.dirize("wwis-cities.json")
        url = 'https://worldweather.wmo.int/en/json/Country_en.json'
        wwis_cities_raw = self._load_check_time(url, wwis_cache_path, "WWIS cities data", self._WWIS_CITIES_REFRESH_INTERVAL)

        if not self._wwis_cities:
            # Process WWIS data to map (lat, lon) -> (cityId, cityName)
            for _membid, member_info in wwis_cities_raw['member'].items():
                if not isinstance(member_info, dict):
                    continue
                for city in member_info['city']:
                    if city['forecast'] == 'Y':
                        lat, lon = float(city['cityLatitude']), float(city['cityLongitude'])
                        self._wwis_cities[(lat, lon)] = city['cityId']

    def _wwis_get_closest_city(self, location, geobackend=None):
        # WWIS equivalent of geocode - finding the closest major city
        try:
            import haversine
        except ImportError as e:
            raise callbacks.Error("This feature requires the 'haversine' Python module - see https://pypi.org/project/haversine/") from e

        latlon = self._geocode(location, geobackend=geobackend)
        if not latlon:
            raise callbacks.Error("Unknown location %s." % location)

        lat, lon, _display_name, _geocodeid, geocode_backend = latlon
        self._wwis_load_cities()

        closest_cities = sorted(self._wwis_cities, key=lambda k: haversine.haversine((lat, lon), k))
        return self._wwis_cities[closest_cities[0]], geocode_backend

    _WWIS_CURRENT_REFRESH_INTERVAL = 300     # 5 minutes
    def _wwis_load_current(self, lang='en'):
        # Load current conditions (wind, humidity, ...)
        # These are served from a separate endpoint with all(!) locations at once!
        wwis_cache_path = conf.supybot.directories.data.dirize("wwis-current.json")
        url = 'https://worldweather.wmo.int/en/json/present.json'
        return self._load_check_time(url, wwis_cache_path, "WWIS current data",
                                     self._WWIS_CURRENT_REFRESH_INTERVAL)


    def _wwis_fetcher(self, location, geobackend=None):
        """Grabs weather data from the World Weather Information Service."""
        cityid, geocode_backend = self._wwis_get_closest_city(location, geobackend=geobackend)

        city_url = f'https://worldweather.wmo.int/en/json/{cityid}_en.json'
        log.debug('NuWeather: fetching current conditions for %s from %s', location, city_url)
        city_data = utils.web.getUrl(city_url, headers=HEADERS).decode('utf-8')
        city_data = json.loads(city_data)
        city_data = city_data['city']
        current_data = self._wwis_load_current()
        display_name = f"{city_data['cityName']}, {city_data['member']['shortMemName'] or city_data['member']['memName']}"

        for current_data_city in current_data['present'].values():
            if current_data_city['cityId'] == cityid:
                break
        else:
            log.error(current_data_city)
            raise ValueError(f"Could not find current conditions for cityID {cityid} ({display_name})")
        return {
            'location': display_name,
            'poweredby': 'WWIS+' + geocode_backend,
            'url': f'https://worldweather.wmo.int/en/city.html?cityId={cityid}',
            'current': {
                'condition': current_data_city["wxdesc"],
                'temperature': formatter.format_temp(c=current_data_city['temp']) if current_data_city['temp'] else _("N/A"),
                'feels_like': _("N/A"),
                'humidity': formatter.format_percentage(current_data_city['rh']) if current_data_city['rh'] else _("N/A"),
                'precip': _("N/A"),
                'wind': formatter.format_distance(km=float(current_data_city['ws'])*3.6, speed=True) if current_data_city['ws'] else _("N/A"),
                'wind_gust': _("N/A"),
                'wind_dir': current_data_city['wd'],
                'uv': _("N/A"),
                'visibility': _("N/A"),
            },
            'forecast': [{'dayname': formatter.get_dayname(forecastdata['forecastDate'], -1,
                                                           fallback=forecastdata['forecastDate']),
                          'max': formatter.format_temp(c=int(forecastdata['maxTemp']) if forecastdata['maxTemp'] else None),
                          'min': formatter.format_temp(c=int(forecastdata['minTemp']) if forecastdata['minTemp'] else None),
                          'summary': forecastdata.get('weather', 'N/A')}
                        for forecastdata in city_data['forecast']['forecastDay']]
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
                'temperature': formatter.format_temp(f=currentdata.get('temperature')),
                'feels_like': formatter.format_temp(f=currentdata.get('apparentTemperature')),
                'humidity': formatter.format_percentage(currentdata.get('humidity')),
                'precip': formatter.format_precip(mm=currentdata.get('precipIntensity')),
                'wind': formatter.format_distance(mi=currentdata.get('windSpeed', 0), speed=True),
                'wind_gust': formatter.format_distance(mi=currentdata.get('windGust', 0), speed=True),
                'wind_dir': formatter.wind_direction(currentdata.get('windBearing')),
                'uv': formatter.format_uv(currentdata.get('uvIndex')),
                'visibility': formatter.format_distance(mi=currentdata.get('visibility')),
            },
            'forecast': [{'dayname': formatter.get_dayname(forecastdata['time'], idx, tz=data['timezone']),
                          'max': formatter.format_temp(f=forecastdata.get('temperatureHigh')),
                          'min': formatter.format_temp(f=forecastdata.get('temperatureLow')),
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

        lat, lon, display_name, _geocode_id, geocode_backend = latlon
        url = 'https://api.openweathermap.org/data/2.5/onecall?' + utils.web.urlencode({
            'appid': apikey,
            'lat': lat,
            'lon': lon,
            'units': 'imperial',
        })
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f, strict=False)

        currentdata = data['current']

        # XXX: are the units for this consistent across APIs?
        if currentdata.get('snow'):
            precip = formatter.format_precip(mm=currentdata['snow']['1h'] * 10)
        elif currentdata.get('rain'):
            precip = formatter.format_precip(mm=currentdata['rain']['1h'])
        else:
            precip = 'N/A'

        output = {
            'location': display_name,
            'poweredby': 'OpenWeatherMap+' + geocode_backend,
            'url': 'https://openweathermap.org/weathermap?' + utils.web.urlencode({
                'lat': lat,
                'lon': lon,
                'zoom': 12
            }),
            'current': {
                'condition': currentdata['weather'][0]['description'],
                'temperature': formatter.format_temp(f=currentdata['temp']),
                'feels_like': formatter.format_temp(f=currentdata['feels_like']),
                'humidity': formatter.format_percentage(currentdata['humidity']),
                'precip': precip,
                'wind': formatter.format_distance(mi=currentdata['wind_speed'], speed=True),
                'wind_dir': formatter.wind_direction(currentdata['wind_deg']),
                'wind_gust': formatter.format_distance(mi=currentdata.get('wind_gust'), speed=True),
                'uv': formatter.format_uv(currentdata.get('uvi')),
                'visibility': formatter.format_distance(km=currentdata['visibility']/1000),
            }
        }

        output['forecast'] = [
            {'dayname': formatter.get_dayname(forecast['dt'], idx, tz=data['timezone']),
             'max': formatter.format_temp(f=forecast['temp']['max']),
             'min': formatter.format_temp(f=forecast['temp']['min']),
             'summary': forecast['weather'][0]['description']}
            for idx, forecast in enumerate(data['daily'])
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

        formatter._channel_context = msg.channel
        backend_func = getattr(self, '_%s_fetcher' % weather_backend)
        raw_data = backend_func(location, geocode_backend)

        s = formatter.format_weather(raw_data, forecast='forecast' in optlist)
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
