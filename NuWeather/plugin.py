###
# Copyright (c) 2018, James Lu <james@overdrivenetworks.com>
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

from supybot import utils, plugins, ircutils, callbacks, world, conf
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NuWeather')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from .config import BACKENDS
from .local import accountsdb

HEADERS = {
    'User-agent': 'Mozilla/5.0 (compatible; Supybot/Limnoria %s; NuWeather weather plugin)' % conf.version
}

class NuWeather(callbacks.Plugin):
    """Weather plugin for Limnoria"""
    threaded = True

    def __init__(self, irc):
        super().__init__(irc)
        # We use 2 DBs: one to store preferred locations and another for location latlon (geocoding)
        self.db = accountsdb.AccountsDB("NuWeather", 'NuWeather.db')
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

    def _format_temp(self, f, c=None, msg=None):
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

        displaymode = self.registryValue('units.temperature', msg.args[0] if msg else None)
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
    def _mangle_temperatures(self, forecast, msg=None):
        """Runs _format_temp() on temperature values embedded within forecast strings."""
        if not forecast:
            return forecast
        for (text, value) in set(self._temperatures_re.findall(forecast)):
            forecast = forecast.replace(text, self._format_temp(f=value, msg=msg))
        return forecast

    @staticmethod
    def _wind_direction(angle):
        """Returns wind direction (N, W, S, E, etc.) given an angle."""
        # Adapted from https://stackoverflow.com/a/7490772
        directions = ('N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW')
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

    def _apixu_fetcher(self, location, msg=None):
        """Grabs weather data from Apixu."""
        apikey = self.registryValue('apikeys.apixu')
        if not apikey:
            raise callbacks.Error(_("Please configure the apixu API key in plugins.nuweather.apikeys.apixu."))
        url = 'https://api.apixu.com/v1/forecast.json?' + utils.web.urlencode({
            'key': apikey,
            'q': location,
        })
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f)

        location = data['location']
        if location['region']:
            location = "%s, %s, %s" % (location['name'], location['region'], location['country'])
        else:
            location = "%s, %s" % (location['name'], location['country'])

        # current conditions
        currentdata = data['current']
        condition = currentdata['condition']['text']
        cur_temp = self._format_temp(currentdata['temp_f'], currentdata['temp_c'], msg=msg)
        feels_like = self._format_temp(currentdata['feelslike_f'], currentdata['feelslike_c'], msg=msg)
        humidity = currentdata['humidity']

        precip = currentdata['precip_mm']
        if float(precip) != 0.0:  # Only show both units if precip > 0
            precip = _('%smm/%sin') % (currentdata['precip_mm'], currentdata['precip_in'])
        else:
            precip = _('%smm') % precip

        wind = currentdata['wind_mph']
        if float(wind) != 0.0:  # Ditto for wind speed
            wind = _('%smph/%skph %s') % (currentdata['wind_mph'], currentdata['wind_kph'], currentdata['wind_dir'])
        else:
            wind = _('%smph') % wind

        visibility = _('%skm/%smi') % (currentdata['vis_km'], currentdata['vis_miles'])
        uv = self._format_uv(currentdata['uv'])

        current = _('%s %s (Humidity: %s%%) | \x02Feels like:\x02 %s | \x02Precip:\x02 %s '
                    '| \x02Wind:\x02 %s | \x02Visibility:\x02 %s | \x02UV:\x02 %s') % (
            condition, cur_temp, humidity, feels_like, precip, wind, visibility, uv
        )

        # daily forecast
        forecastdata = data['forecast']['forecastday'][0]
        condition = forecastdata['day']['condition']['text']
        maxtemp = self._format_temp(forecastdata['day']['maxtemp_f'], forecastdata['day']['maxtemp_c'], msg=msg)
        mintemp = self._format_temp(forecastdata['day']['mintemp_f'], forecastdata['day']['mintemp_c'], msg=msg)
        forecast = _('%s; High: %s Low: %s' % (condition, maxtemp, mintemp))

        s = _('%s :: %s | \x02Today:\x02 %s | Powered by \x02Apixu\x02') % (
            ircutils.bold(location), current, forecast
        )
        return s

    def _darksky_fetcher(self, location, msg=None):
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
        summary = currentdata.get('summary', 'N/A')
        temp = currentdata.get('temperature')
        if temp is not None:
            temp = self._format_temp(temp, msg=msg)
        else:
            temp = ''  # Not available

        s = '%s :: %s %s' % (ircutils.bold(display_name), summary, temp)

        humidity = currentdata.get('humidity')
        if humidity is not None:  # Format humidity as a percentage
            s += _(' (\x02Humidity:\x02 %.0f%%)') % (float(humidity) * 100)

        feels_like = currentdata.get('apparentTemperature')
        if feels_like is not None:
            feels_like = self._format_temp(feels_like, msg=msg)
            s += _(' | \x02Feels like:\x02 %s') % feels_like

        precip = currentdata.get('precipIntensity')  # mm per hour
        if precip is not None:
            s += _(' | \x02Precip:\x02 %smm') % precip

        wind_str = ''
        windspeed = currentdata.get('windSpeed', 0)
        windgust = currentdata.get('windGust', 0)
        if windspeed:
            wind_str = _(' | \x02Wind:\x02 %smph') % windspeed
            windbearing = currentdata.get('windBearing')  # This can only be defined if windSpeed != 0
            if windbearing:
                wind_str += ' '
                wind_str += self._wind_direction(windbearing)
            if windgust:
                wind_str += _(' up to %smph') % windgust
        s += wind_str

        visibility = currentdata.get('visibility')
        if visibility is not None:
            s += _(' | \x02Visibility:\x02 %smi') % visibility

        uv = currentdata.get('uvIndex')
        if uv is not None:
            s += _(' | \x02UV:\x02 %s') % self._format_uv(uv)

        if data['hourly'].get('summary'):
            hourly_summary = self._mangle_temperatures(data['hourly']['summary'], msg=msg)
            s += _(' | \x02This hour\x02: %s' % hourly_summary)
        if data['daily'].get('summary'):
            daily_summary = self._mangle_temperatures(data['daily']['summary'], msg=msg)
            s += _(' | \x02Today\x02: %s' % daily_summary)

        url = 'https://darksky.net/forecast/%s,%s' % (lat, lon)
        s += _(format(' | Powered by \x02Dark Sky+%s\x02 %u', self._geocode.backend, url))
        return s

    @wrap([getopts({'user': 'nick', 'backend': None}), additional('text')])
    def weather(self, irc, msg, args, optlist, location):
        """
        [--user <othernick>] [--backend <backend>] [<location>]

        Fetches weather and forecast information for <location>. <location> can be left blank if you have a previously set location (via 'setweather').

        If the --user option is specified, show weather for the saved location of that nick, instead of the caller.
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
            irc.error(_("I did not find a preset location for your nick. Please set one via 'setweather <location>'."), Raise=True)

        backend = optlist.get('backend', self.registryValue('defaultBackend', msg.args[0]))
        if backend not in BACKENDS:
            irc.error(_("Unknown weather backend %s. Valid ones are: %s") % (backend, ', '.join(BACKENDS)), Raise=True)

        backend_func = getattr(self, '_%s_fetcher' % backend)
        s = backend_func(location, msg=msg)
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
