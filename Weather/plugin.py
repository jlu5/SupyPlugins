# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2014, spline
# Copyright (c) 2014-2018, James Lu <james@overdrivenetworks.com>
# All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###


from __future__ import unicode_literals
import json
from math import floor
import sqlite3
import string
try:
    from itertools import izip
except ImportError:  # Python 3
    izip = zip

import supybot.conf as conf
import supybot.log as log
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weather')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x


class WeatherDB():
    """WeatherDB class to store our users and their settings."""

    def __init__(self):
        self.filename = conf.supybot.directories.data.dirize("Weather.db")
        self.log = log.getPluginLogger('Weather')
        self._conn = sqlite3.connect(self.filename, check_same_thread=False)
        self._conn.text_factory = str
        self.makeDb()

    def makeDb(self):
        """Create our DB."""

        self.log.info("Weather: Checking/Creating DB.")
        with self._conn as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                          nick TEXT PRIMARY KEY,
                          location TEXT NOT NULL,
                          metric INTEGER DEFAULT 0,
                          alerts INTEGER DEFAULT 0,
                          almanac INTEGER DEFAULT 0,
                          astronomy INTEGER DEFAULT 0,
                          forecast INTEGER DEFAULT 0,
                          pressure INTEGER DEFAULT 0,
                          wind INTEGER DEFAULT 0,
                          uv INTEGER DEFAULT 0,
                          visibility INTEGER DEFAULT 0,
                          dewpoint INTEGER DEFAULT 0,
                          humidity INTEGER DEFAULT 0,
                          updated INTEGER DEFAULT 0)""")
            self._conn.commit()  # this fails silently if already there.
            # next, we see if we need to upgrade the old table structure.
            cursor = conn.cursor()  # the old table is 4.
            tablelength = len([l[1] for l in cursor.execute("pragma table_info('users')").fetchall()])
            if tablelength == 4:  # old table is 4: users, location, metric, colortemp.
                self.log.info("Weather: Upgrading database version.")
                columns = ['alerts', 'almanac', 'astronomy', 'forecast', 'pressure', 'wind', 'uv', 'visibility', 'dewpoint', 'humidity', 'updated']
                for column in columns:
                    try:
                        cursor.execute('ALTER TABLE users ADD COLUMN %s INTEGER DEFAULT 0' % column)
                        self._conn.commit()
                    except:  # fail silently.
                        pass

    def setweather(self, username, location):
        """Stores or update a user's location. Adds user if not found."""
        with self._conn as conn:
            cursor = conn.cursor()
            if self.getuser(username):  # username exists.
                cursor.execute("""UPDATE users SET location=? WHERE nick=?""", (location, username,))
            else:  # username does not exist so add it in.
                cursor.execute("""INSERT OR REPLACE INTO users (nick, location) VALUES (?,?)""", (username, location,))
            self._conn.commit()  # commit.

    def setsetting(self, username, setting, value):
        """Set one of the user settings."""

        with self._conn as conn:
            cursor = conn.cursor()
            query = "UPDATE users SET %s=? WHERE nick=?" % setting
            cursor.execute(query, (value, username,))
            self._conn.commit()

    def getsettings(self):
        """Get all 'user' settings that can be set."""

        with self._conn as conn:
            cursor = conn.cursor()  # below, we get all column names that are settings (INTEGERS)
            settings = [str(l[1]) for l in cursor.execute("pragma table_info('users')").fetchall() if l[2] == "INTEGER"]
            return settings

    def getweather(self, user):
        """Return a dict of user's settings."""
        self._conn.row_factory = sqlite3.Row
        with self._conn as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT * from users where nick=?""", (user,))
            row = cursor.fetchone()
            if not row:  # user does not exist.
                return None
            else:  # user exists.
                rowdict = dict(izip(row.keys(), row))
                return rowdict

    def getuser(self, user):
        """Returns a boolean if a user exists."""
        with self._conn as conn:
            cursor = conn.cursor()
            cursor.execute("""SELECT location from users where nick=?""", (user,))
            row = cursor.fetchone()
            if row:
                return True
            else:
                return False


class WeatherAPIError(RuntimeError):
    pass

class Weather(callbacks.Plugin):
    """This plugin provides access to information from Weather Underground."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Weather, self)
        self.__parent.__init__(irc)
        self.db = WeatherDB()

    ##############
    # FORMATTING #
    ##############

    def _bold(self, string):
        return ircutils.bold(string)

    def _bu(self, string):
        return ircutils.underline(ircutils.bold(string))

    ############################
    # INTERNAL WEATHER HELPERS #
    ############################

    def _temp(self, channel, f, c=None):
        """Returns a colored string based on the temperature."""

        # lets be safe and wrap in a try/except because we can't always trust data purity.
        try:
            if str(f).startswith('NA'): # Wunderground sends a field that's not available
                return f
            f = int(f)
            if not c:
                c = int((f - 32) * 5/9)
            s = "{0}F/{1}C".format(f, c)
            # determine color.
            if not self.registryValue('disableColoredTemp', channel):
                if f < 10.0:
                    color = 'light blue'
                elif 10.0 <= f <= 32.0:
                    color = 'teal'
                elif 32.1 <= f <= 50.0:
                    color = 'blue'
                elif 50.1 <= f <= 60.0:
                    color = 'light green'
                elif 60.1 <= f <= 70.0:
                    color = 'green'
                elif 70.1 <= f <= 80.0:
                    color = 'yellow'
                elif 80.1 <= f <= 90.0:
                    color = 'orange'
                elif f > 90.0:
                    color = 'red'
                else:
                    color = 'light grey'
                s = ircutils.mircColor(s, color)
            # return.
            return s
        except (TypeError, ValueError) as e:
            self.log.info("Weather: ValueError trying to convert temp: {0} message: {1}".format(f, e))
            return "N/A"

    def _wind(self, angle, useSymbols=False):
        """Converts degrees to direction for wind. Can optionally return a symbol."""

        if not useSymbols:  # ordinal names.
            direction_names = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        else:  # symbols.
            direction_names = ['↑', '↗', '→', '↘', '↓', '↙', '←', '↖']
        # do math below to figure the angle->direction out.
        directions_num = len(direction_names)
        directions_step = 360./directions_num
        index = int(round((angle/360. - floor(angle/360.)*360.)/directions_step))
        index %= directions_num
        # return.
        return direction_names[index]

    @staticmethod
    def _format_geolookup_name(result):
        """Formats a place name from Wunderground Geolookup."""
        if result['state'] and not result['state'].isdigit():
            template = '{city}, {state}, {country_name}'
        else:
            template = '{city}, {country_name}'
        return template.format(**result)

    ##############################################
    # PUBLIC FUNCTIONS TO WORK WITH THE DATABASE #
    ##############################################

    def setuser(self, irc, msg, args, optset, optbool):
        """<setting> <True|False>

        Sets a user's <setting> to True or False.
        Valid settings include: alerts, almanac, astronomy, forecast, pressure,
        wind, uv, visibility, dewpoint, humidity, and updated.
        """

        # first, lower
        optset = optset.lower()
        # grab a list of valid settings.
        validset = self.db.getsettings()
        if optset not in validset:
            irc.error(format("%r is an invalid setting. Must be one of: %L.", optset,
                      sorted(validset)), Raise=True)
        if optbool:  # True.
            value = 1
        else:  # False.
            value = 0
        # check user first.
        if not self.db.getuser(msg.nick.lower()):  # user exists
            irc.error("You are not in the database; you must use 'setweather' first.", Raise=True)
        else:  # user is valid. perform the op.
            self.db.setsetting(msg.nick.lower(), optset, value)
            irc.replySuccess()

    setuser = wrap(setuser, [('somethingWithoutSpaces'), ('boolean')])

    def setweather(self, irc, msg, args, optlocation):
        """<location code>

        Sets the weather location for your nick. Location codes can be city names, "City, Country"
        pairs, ICAO airport codes, US ZIP codes, or raw zmw codes as returned by the
        'locationsearch' command.
        """
        self.db.setweather(msg.nick.lower(), optlocation)
        irc.replySuccess()

    setweather = wrap(setweather, [('text')])

    ##########################
    # WUNDERGROUND API CALLS #
    ##########################

    def _wuac(self, q, return_names=False):
        """Internal helper to find locations via Wunderground's GeoLookup API.
        Previous versions of this plugin used the Autocompete API instead."""

        if q.startswith('zmw:'):
            # If we're given a ZMW code, just return it as is.
            return [q]

        apikey = self.registryValue('apiKey')
        if not apikey:
            raise callbacks.Error("No Wunderground API key was defined; set "
                                  "the 'plugins.Weather.apiKey' config variable.")

        url = 'http://api.wunderground.com/api/%s/geolookup/q/%s.json' % (apikey, utils.web.urlquote(q))
        self.log.debug("Weather: GeoLookup URL %s", url)
        page = utils.web.getUrl(url, timeout=5)
        data = json.loads(page.decode('utf-8'))

        if data.get('location'):
            # This form is used when there's only one result.
            zmw = 'zmw:{zip}.{magic}.{wmo}'.format(**data['location'])
            if return_names:
                name = self._format_geolookup_name(data['location'])
                return [(name, zmw)]
            else:
                return [zmw]
        else:
            if data['response'].get('error'):
                errdata = data['response']['error']
                raise WeatherAPIError('Error in _wuac step: [%s] %s' %
                                      (errdata.get('type', 'N/A'),
                                       errdata.get('description', 'No message specified')))
            # This form of result is returned there are multiple places matching a query
            results = data['response'].get('results')
            if not results:
                return []

            if return_names:
                results = [(self._format_geolookup_name(result), 'zmw:' + result['zmw']) for result in results]
            else:
                results = [('zmw:' + result['zmw']) for result in results]
            return results


    ####################
    # PUBLIC FUNCTIONS #
    ####################

    @wrap([getopts({'user': 'nick'}), optional('text')])
    def weather(self, irc, msg, args, optlist, location):
        """[<location>] [--user <othernick>]

        Fetches weather and forecast information for <location>. <location> can be left blank if you have a previously set location (via 'setweather').

        If the --user option is specified, show weather for the saved location of that nick, instead of the caller.

        Location can take many forms, including a simple city name, US state/city (CA/San_Francisco), zip code, country/city (Australia/Sydney), or an airport code (KJFK).
        Ex: 10021 or Sydney, Australia or KJFK
        """
        apikey = self.registryValue('apiKey')
        if not apikey:
            irc.error("No Wunderground API key was defined; set the 'plugins.Weather.apiKey' config variable.",
                      Raise=True)
        channel = msg.args[0]

        optlist = dict(optlist)
        # Default to looking at the caller's saved info, but optionally they can look at someone else's weather too.
        nick = optlist.get('user') or msg.nick

        # urlargs will be used to build the url to query the API.
        # besides lang, these are preset values that should not be changed.
        urlArgs = {'features': ['conditions', 'forecast'],
                   'lang': self.registryValue('lang'),
                   'bestfct': '1',
                   'pws': '0' }

        loc = None
        args = {'imperial': self.registryValue('useImperial', msg.args[0]),
                'alerts': self.registryValue('alerts'),
                'almanac': self.registryValue('almanac'),
                'astronomy': self.registryValue('astronomy'),
                'pressure': self.registryValue('showPressure'),
                'wind': self.registryValue('showWind'),
                'updated': self.registryValue('showUpdated'),
                'forecast': False,
                'humidity': False,
                'uv': False,
                'visibility': False,
                'dewpoint': False}

        usersetting = self.db.getweather(nick.lower())
        if usersetting:
            for (k, v) in usersetting.items():
                args[k] = v
            # Prefer the location given in the command, falling back to the one stored in the DB if not given.
            location = location or usersetting["location"]
            args['imperial'] = (not usersetting["metric"])
        # If both command line and DB locations aren't given, bail.
        if not location:
            if nick != msg.nick:
                irc.error("I did not find a preset location for %s." % nick, Raise=True)
            else:
                irc.error("I did not find a preset location for you. Set one via 'setweather <location>'.", Raise=True)

        loc = self._wuac(location)
        if not loc:
            irc.error("Failed to find a valid location for: %r" % location, Raise=True)
        else:
            # Use the first location.
            loc = loc[0]

        for check in ['alerts', 'almanac', 'astronomy']:
            if args[check]:
                urlArgs['features'].append(check) # append to dict->key (list)

        baseurl = 'http://api.wunderground.com/api/%s/' % apikey

        # Prepare API options
        for (key, value) in urlArgs.items():
            if key == "features": # will always be at least conditions.
                # Join features directly to the URL
                baseurl += "/".join(value)
                baseurl += "/"
            if key in ("lang", "bestfct", "pws"):
                # Preset and configured (only lang) options,  added with key:value
                baseurl += "{0}:{1}/".format(key, value)

        url = '%s/q/%s.json' % (baseurl.rstrip('/'), loc)
        self.log.debug("Weather URL: {0}".format(url))
        page = utils.web.getUrl(url, timeout=5)
        data = json.loads(page.decode('utf-8'))

        if data['response'].get('error'):
            errdata = data['response']['error']
            raise WeatherAPIError('Error in weather step: [%s] %s' %
                                  (errdata.get('type', 'N/A'),
                                   errdata.get('description', 'No message specified')))
        elif 'current_observation' not in data:
            irc.error("Failed to fetch current conditions for %r." % loc, Raise=True)

        outdata = {'weather': data['current_observation']['weather'],
                   'location': data['current_observation']['display_location']['full'],
                   'humidity': data['current_observation']['relative_humidity'],
                   'uv': data['current_observation']['UV']}

        if data['current_observation']['wind_mph'] < 1:  # no wind.
            outdata['wind'] = "None"
        else:
            if args['imperial']:
                outdata['wind'] = "{0}@{1}mph".format(self._wind(data['current_observation']['wind_degrees']), data['current_observation']['wind_mph'])
                if int(data['current_observation']['wind_gust_mph']) > 0:
                    outdata['wind'] += " ({0}mph gusts)".format(data['current_observation']['wind_gust_mph'])
            else:
                outdata['wind'] = "{0}@{1}kph".format(self._wind(data['current_observation']['wind_degrees']),data['current_observation']['wind_kph'])
                if int(data['current_observation']['wind_gust_kph']) > 0:
                    outdata['wind'] += " ({0}kph gusts)".format(data['current_observation']['wind_gust_kph'])

        # Show the last updated time if available.
        observationTime = data['current_observation'].get('observation_epoch')
        localTime = data['current_observation'].get('local_epoch')

        if not observationTime or not localTime:
            outdata['observation'] = data.get('observation_time', 'unknown').lstrip('Last Updated on ')
        else:  # Prefer relative times, if available
            s = int(localTime) - int(observationTime)  # format into seconds.
            if s <= 1:
                outdata['observation'] = 'just now'
            elif s < 60:
                outdata['observation'] = '{0}s ago'.format(s)
            elif s < 120:
                outdata['observation'] = '1m ago'
            elif s < 3600:
                outdata['observation'] = '{0}m ago'.format(s/60)
            elif s < 7200:
                outdata['observation'] = '1hr ago'
            else:
                outdata['observation'] = '{0}hrs ago'.format(s/3600)

        outdata['temp'] = self._temp(channel, data['current_observation']['temp_f'])

        # pressure.
        pin = str(data['current_observation']['pressure_in']) + 'in'
        pmb = str(data['current_observation']['pressure_mb']) + 'mb'
        outdata['pressure'] = "{0}/{1}".format(pin, pmb)

        # dewpoint.
        outdata['dewpoint'] = self._temp(channel, data['current_observation']['dewpoint_f'])

        # heatindex.
        outdata['heatindex'] = self._temp(channel, data['current_observation']['heat_index_f'])

        # windchill.
        outdata['windchill'] = self._temp(channel, data['current_observation']['windchill_f'])

        # feels like
        outdata['feelslike'] = self._temp(channel, data['current_observation']['feelslike_f'])

        # visibility.
        vmi = str(data['current_observation']['visibility_mi']) + 'mi'
        vkm = str(data['current_observation']['visibility_km']) + 'km'
        outdata['visibility'] = "{0}/{1}".format(vmi, vkm)

        # handle forecast data. This is internally stored as a dict with integer keys (days from now)
        # with the forecast text as values.
        forecastdata = {}
        if 'forecast' in data:
            for forecastday in data['forecast']['txt_forecast']['forecastday']:
                # Slightly different wording and results (e.g. rainfall for X inches vs. X cm) are given
                # depending on whether imperial or metric units are the same.
                if args['imperial']:
                    text = forecastday['fcttext']
                else:
                    text = forecastday['fcttext_metric']
                forecastdata[int(forecastday['period'])] = {'day': forecastday['title'],
                                                            'text': text}

        output = "{0} :: {1} ::".format(self._bold(outdata['location']), outdata['weather'])
        output += " {0} ".format(outdata['temp'])

        # humidity.
        if args['humidity']:
            output += "(Humidity: {0}) ".format(outdata['humidity'])

        # windchill/heatindex are conditional on season but test with startswith to see what to include
        # NA means not available, so ignore those fields
        if not outdata['windchill'].startswith("NA"):
            output += "| {0} {1} ".format(self._bold('Wind Chill:'), outdata['windchill'])
        if not outdata['heatindex'].startswith("NA"):
            output += "| {0} {1} ".format(self._bold('Heat Index:'), outdata['heatindex'])

        # Iterate over the args dict for what extra data to include
        for k in ('wind', 'visibility', 'uv', 'pressure', 'dewpoint'):
            if args[k]:
                output += "| {0}: {1} ".format(self._bold(k.title()), outdata[k])

        if forecastdata:
            # Add in the first two forecasts item in conditions + the "last updated" time.
            output += "| {0}: {1}".format(self._bold(forecastdata[0]['day']), forecastdata[0]['text'])
            output += " {0}: {1}".format(self._bold(forecastdata[1]['day']), forecastdata[1]['text'])

        if args['updated']:
            # Round updated time (given as a string) to the nearest unit.
            # This is annoying because Wunderground sends these as raw strings, in the form
            # "1hr ago" or "2.7666666666666666m ago"
            tailstr = outdata['observation'].lstrip(string.digits + '.')
            updated_time = outdata['observation'].rstrip(string.ascii_letters + ' ')
            try:
                updated_time = round(float(updated_time))
            except ValueError:
                pass
            output += " | Updated %s%s" % (ircutils.bold(updated_time), tailstr)

        # finally, output the basic weather.
        irc.reply(output)

        # handle alerts - everything here and below sends as separate replies if enabled
        if args['alerts'] and data['alerts']:  # only look for alerts if enabled and present.
            outdata['alerts'] = data['alerts'][0]['message']  # need to do some formatting below.
            outdata['alerts'] = outdata['alerts'].replace('\n', ' ')
            outdata['alerts'] = utils.str.normalizeWhitespace(outdata['alerts'])  # fix pesky double whitespacing.
            irc.reply("{0} {1}".format(self._bu("Alerts:"), outdata['alerts']))

        # handle almanac
        if args['almanac']:
            try:
                outdata['highyear'] = data['almanac']['temp_high'].get('recordyear')
                outdata['lowyear'] = data['almanac']['temp_low'].get('recordyear')
                outdata['highaverage'] = self._temp(channel, data['almanac']['temp_high']['normal']['F'])
                outdata['lowaverage'] = self._temp(channel, data['almanac']['temp_low']['normal']['F'])
                if outdata['highyear'] != "NA" and outdata['lowyear'] != "NA":
                    outdata['highrecord'] = self._temp(channel, data['almanac']['temp_high']['record']['F'])
                    outdata['lowrecord'] = self._temp(channel, data['almanac']['temp_low']['record']['F'])
                else:
                    outdata['highrecord'] = outdata['lowrecord'] = "NA"
            except KeyError:
                output = "%s Not available." % self._bu('Almanac:')
            else:
                output = ("{0} Average High: {1} (Record: {2} in {3}) | Average Low: {4} (Record: {5} in {6})".format(
                          self._bu('Almanac:'), outdata['highaverage'], outdata['highrecord'], outdata['highyear'],
                          outdata['lowaverage'], outdata['lowrecord'], outdata['lowyear']))
            irc.reply(output)

        # handle astronomy
        if args['astronomy']:
            sunriseh = data['moon_phase']['sunrise']['hour']
            sunrisem = data['moon_phase']['sunrise']['minute']
            sunseth = data['moon_phase']['sunset']['hour']
            sunsetm = data['moon_phase']['sunset']['minute']
            sunrise = "{0}:{1}".format(sunriseh, sunrisem)
            sunset = "{0}:{1}".format(sunseth, sunsetm)
            # Oh god, this one-liner... -GLolol
            lengthofday = "%dh%dm" % divmod((((int(sunseth)-int(sunriseh))+float((int(sunsetm)-int(sunrisem))/60.0))*60 ),60)
            astronomy = {'Moon illum:': str(data['moon_phase']['percentIlluminated']) + "%",
                         'Moon age:': str(data['moon_phase']['ageOfMoon']) + "d",
                         'Sunrise:': sunrise,
                         'Sunset:': sunset,
                         'Length of Day:': lengthofday}
            output = [format('%s %s', self._bold(k), v) for k, v in sorted(astronomy.items())]
            output = format("%s %s", self._bu('Astronomy:'), " | ".join(output))
            irc.reply(output)

        # handle forecast
        if args['forecast']:
            fullforecastdata = {}  # key = day (int), value = dict of forecast data.
            for forecastday in data['forecast']['simpleforecast']['forecastday']:
                high = self._temp(channel, forecastday['high']['fahrenheit'])
                low = self._temp(channel, forecastday['low']['fahrenheit'])
                tmpdict = {'day': forecastday['date']['weekday_short'],
                           'text': forecastday['conditions'],
                           'low': low,
                           'high': high}
                fullforecastdata[int(forecastday['period'])] = tmpdict
            outforecast = [] # prep string for output.

            for (k, v) in fullforecastdata.items(): # iterate through forecast data.
                outforecast.append("{0}: {1} (High: {2} Low: {3})".format(self._bold(v['day']),
                        v['text'], v['high'], v['low']))
            output = "{0} {1}".format(self._bu('Forecast:'), " | ".join(outforecast))
            irc.reply(output)

    @wrap(['text'])
    def locationsearch(self, irc, msg, args, text):
        """<location>

        Returns a list of raw Wunderground (ZMW) codes given the search query <location>. This can be
        helpful if Wunderground's autocomplete is not picking up the right place, as you can directly
        look up weather using any ZMW codes returned here.

        Warning: ZMW codes are not fixed and are prone to sudden changes!
        """
        apikey = self.registryValue('apiKey')
        if not apikey:
            irc.error("No Wunderground API key was defined; set 'config plugins.Weather.apiKey'.",
                      Raise=True)

        results = self._wuac(text, return_names=True)
        if not results:
            irc.error("No results found.")
        else:
            irc.reply(format('%L', ('\x02{0}\x02: {1}'.format(*result) for result in results)))

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
