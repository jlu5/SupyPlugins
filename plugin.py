# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2014, spline
# All rights reserved.
###
# my libs
import json  # json.
from math import floor  # for wind.
import sqlite3  # userdb.
from itertools import izip  # userdb.
# extra supybot libs
import supybot.conf as conf
import supybot.log as log
# supybot libs
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

        self.log.info("WeatherDB: Checking/Creating DB.")
        with self._conn as conn:
            cursor = conn.cursor()
            cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                          nick TEXT PRIMARY KEY,
                          location TEXT NOT NULL,
                          metric INTEGER DEFAULT 0,
                          colortemp INTEGER DEFAULT 1,
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
                self.log.info("Table length is 4. We need to upgrade.")
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


class Weather(callbacks.Plugin):
    """Add the help for "@plugin help Weather" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Weather, self)
        self.__parent.__init__(irc)
        self.APIKEY = self.registryValue('apiKey')
        self.db = WeatherDB()

    def die(self):
        self.__parent.die()

    ##############
    # FORMATTING #
    ##############

    def _bold(self, string):
        return ircutils.bold(string)

    def _bu(self, string):
        return ircutils.underline(ircutils.bold(string))

    def _strip(self, string):
        return ircutils.stripFormatting(string)

    ############################
    # INTERNAL WEATHER HELPERS #
    ############################

    def _weatherSymbol(self, code):
        """Return a unicode symbol based on weather status."""

        table = {'partlycloudy':'~☁',
                 'cloudy':'☁',
                 'tstorms':'⚡',
                 'sunny':'☀',
                 'snow':'❄',
                 'sleet':'☄',
                 'rain':'☔',
                 'mostlysunny':'~☀',
                 'mostlycloudy':'~☁',
                 'hazy':'♒',
                 'fog':'♒',
                 'flurries':'❄',
                 'clear':'☼',
                 'chanceflurries':'?❄',
                 'chancerain':'?☔',
                 'chancesleet':'?❄',
                 'chancesnow':'?❄',
                 'chancetstorms':'?☔' }
        # return symbol from table.
        try:
            return table[code]
        except KeyError:
            return "unknown"

    def _moonphase(self, phase):
        """Returns a moon phase based on the %."""

        # depending on the phase float, we have an ascii picture+text to represent it.
        if phase < 0.05:
            symbol = "[ (  ) ] (fullmoon)"
        elif phase < 0.20:
            symbol = "[ C   ] (decreasing moon)"
        elif phase < 0.30:
            symbol = "[ C   ] (half moon)"
        elif phase < 0.45:
            symbol = "[ (   ] (decreasing moon)"
        elif phase < 0.65:
            symbol = "[     ] (new moon)"
        elif phase < 0.80:
            symbol = "[   ) ] (waxing moon)"
        elif phase < 0.80:
            symbol = "[   D ] (half moon)"
        else:
            symbol = "[   D ] (waxing moon)"
        # return.
        return symbol

    def _temp(self, x):
        """Returns a colored string based on the temperature."""

        # lets be safe and wrap in a try/except because we can't always trust data purity.
        try:
            # first, convert into F so we only have one table.
            if x.endswith('C'):  # c.
                x = float(str(x).replace('C', '')) * 9 / 5 + 32  # remove C + math into float(F).
                unit = "C"
            else:  # f.
                x = float(str(x).replace('F', ''))  # remove F. str->float.
                unit = "F"
            # determine color.
            if x < 10.0:
                color = 'light blue'
            elif 10.0 <= x <= 32.0:
                color = 'teal'
            elif 32.1 <= x <= 50.0:
                color = 'blue'
            elif 50.1 <= x <= 60.0:
                color = 'light green'
            elif 60.1 <= x <= 70.0:
                color = 'green'
            elif 70.1 <= x <= 80.0:
                color = 'yellow'
            elif 80.1 <= x <= 90.0:
                color = 'orange'
            elif x > 90.0:
                color = 'red'
            else:
                color = 'light grey'
            # return.
            if unit == "F":  # no need to convert back.
                return ircutils.mircColor(("{0:.0f}F".format(x)), color)
            else:  # temp is in F and we need to go back to C.
                return ircutils.mircColor(("{0:.0f}C".format((x - 32) * 5 / 9)),color)
        except Exception, e:  # rutroh. something went wrong.
            self.log.info("_temp: ERROR trying to convert temp: {0} message: {1}".format(x, e))
            return x
    
    def _tw(self, bol, x):
        """This is a convenience handle that wraps _temp."""
        
        # make sure we have 'bol', which should come in from args['nocolortemp'].
        # since the option is a negation, we assume NO.
        if not bol:  # COLOR IT.
            x = self._temp(x)
            return x
        else:
            return x

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

    ##############################################
    # PUBLIC FUNCTIONS TO WORK WITH THE DATABASE #
    ##############################################

    def setuser(self, irc, msg, args, optset, optbool):
        """<setting> <True|False>

        Sets a user's <setting> to True or False.
        Settings: alerts, almanac, astronomy, forecast, pressure, wind, uv, visibility, dewpoint, humidity, updated
        Ex: metric True or colortemp False
        """

        # first, lower
        optset = optset.lower()
        # grab a list of valid settings.
        validset = self.db.getsettings()
        if optset not in validset:
            irc.reply("ERROR: '{0}' is an invalid setting. Must be one of: {1}".format(optset, " | ".join(sorted([i for i in validset]))))
            return
        # setting value True/False
        if optbool:  # True.
            value = 1
        else:  # False.
            value = 0
        # check user first.
        if not self.db.getuser(msg.nick.lower()):  # user exists
            irc.reply("ERROR: You're not in the database. You must setweather first.")
        else:  # user is valid. perform the op.
            self.db.setsetting(msg.nick.lower(), optset, value)
            irc.reply("I have changed {0}'s {1} setting to {2}".format(msg.nick, optset, value))

    setuser = wrap(setuser, [('somethingWithoutSpaces'), ('boolean')])

    def setweather(self, irc, msg, args, optlocation):
        """<location code>
        Set's weather location code for your nick as location code.

        Use your zip/postal code to keep it simple.
        Ex: setweather 10012
        """

        # set the weather id based on nick. This will update or set.
        self.db.setweather(msg.nick.lower(), optlocation)
        irc.reply("I have changed {0}'s weather ID to {1}".format(msg.nick.lower(), optlocation))

    setweather = wrap(setweather, [('text')])

    ##########################
    # WUNDERGROUND API CALLS #
    ##########################

    def _wuac(self, q):
        """Internal helper to find a location via Wunderground's autocomplete API."""

        url = 'http://autocomplete.wunderground.com/aq?query=%s' % utils.web.urlquote(q)
        #self.log.info("WUAC URL: {0}".format(url))
        # try and fetch.
        try:
            page = utils.web.getUrl(url)
        except Exception, e:  # something didn't work.
            self.log.info("_wuac: ERROR: Trying to open {0} message: {1}".format(url, e))
            return None
        # now process json and return.
        try:
            data = json.loads(page.decode('utf-8'))
            loc = data['RESULTS'][0]['zmw']  # find the first zmw.
            loc = "zmw:%s" % loc  # return w/zmw: attached.
            return loc
        except Exception, e:
            self.log.info("_wuac: ERROR processing json in {0} :: {1}".format(url, e))
            return None

    def _wunderjson(self, url, location):
        """Fetch wunderground JSON and return."""

        # first, construct the url properly.
        if url.endswith('/'):  # cheap way to strip the tailing /
            url = '%sq/%s.json' % (url, utils.web.urlquote(location))
        else:
            url = '%s/q/%s.json' % (url, utils.web.urlquote(location))
        # now actually fetch the url.
        try:
            self.log.info("URL: {0}".format(url))
            page = utils.web.getUrl(url)
            return page
        except Exception, e:  # something didn't work.
            self.log.info("_wunderjson: ERROR Trying to open {0} message: {1}".format(url, e))
            return None

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def wunderground(self, irc, msg, args, optlist, optinput):
        """[--options] <location>

        Fetch weather and forcast information for <location>

        Location must be one of: US state/city (CA/San_Francisco), zipcode, country/city (Australia/Sydney), airport code (KJFK)
        Use --help to list all options.
        Ex: 10021 or Sydney, Australia or KJFK
        """

        # first, check if we have an API key. Useless w/o this.
        if len(self.APIKEY) < 1 or not self.APIKEY or self.APIKEY == "Not set":
            irc.reply("ERROR: Need a Wunderground API key. Set config plugins.Weather.apiKey and reload Weather.")
            return

        # urlargs will be used to build the url to query the API.
        # besides lang, these are unmutable values that should not be changed.
        urlArgs = {'features':['conditions', 'forecast'],
                   'lang':self.registryValue('lang'),
                   'bestfct':'1',
                   'pws':'0' }
        # now, figure out the rest of the options for fetching and displaying weather.
        # some of these are for the query and the others are for output.
        # the order will always go global->channel (supybot config) -> user.
        loc = None
        args = {'imperial':self.registryValue('useImperial', msg.args[0]),
                'nocolortemp':self.registryValue('disableColoredTemp', msg.args[0]),
                'alerts':self.registryValue('alerts'),
                'almanac':self.registryValue('almanac'),
                'astronomy':self.registryValue('astronomy'),
                'pressure':self.registryValue('showPressure'),
                'wind':self.registryValue('showWind'),
                'updated':self.registryValue('showUpdated'),
                'showImperialAndMetric':self.registryValue('showImperialAndMetric', msg.args[0]),
                'forecast':False,
                'humidity':False,
                'strip':False,
                'uv':False,
                'visibility':False,
                'dewpoint':False }

        # instead of doing optlist, we need to handle the location/options to set initially.
        # first, check if there is a user so we can grab their settings.
        usersetting = self.db.getweather(msg.nick.lower())  # check the db.
        if usersetting:  # user is found. lets grab their location and settings.
                for (k, v) in usersetting.items():  # iterate over settings dict returned from getweather row.
                     # set specific settings based on keys that won't 1:1 match.
                    if k == 'location':  # location. look down below this for how the logic is handled.
                        loc = v  # copy over their location from the DB to loc.
                    elif k == 'metric':  # metric
                        if v == 1:  # true.
                            args['imperial'] = False
                        else:  # 0 = false.
                            args['imperial'] = True
                    elif k == 'colortemp':  # colortemp.
                        if v == 1:  # true.
                            args['nocolortemp'] = False
                        else:  # false. the 'nocolortemp' values are inverse.
                            args['nocolortemp'] = True
                    else:  # rest of them are 1:1.
                        if v == 1:  # if value is 1, or true.
                            args[k] = True
                        else:  # argument is 0 or False.
                            args[k] = False
        else:  # user was not found.
            if not optinput:  # location was also not specified, so we must bail.
                irc.reply("ERROR: I did not find a preset location for you. Set via setweather <location>")
                return

        # handle optlist (getopts). this will manipulate output via args dict.
        # we must do this after the dblookup for users as it would always override.
        if optlist:
            for (key, value) in optlist:
                if key == "metric":
                    args['imperial'] = False
                if key == 'alerts':
                    args['alerts'] = True
                if key == 'forecast':
                    args['forecast'] = True
                if key == 'almanac':
                    args['almanac'] = True
                if key == 'pressure':
                    args['pressure'] = True
                if key == 'humidity':
                    args['humidity'] = True
                if key == 'wind':
                    args['wind'] = True
                if key == 'uv':
                    args['uv'] = True
                if key == 'visibility':
                    args['visibility'] = True
                if key == 'dewpoint':
                    args['dewpoint'] = True
                if key == 'astronomy':
                    args['astronomy'] = True
                if key == 'nocolortemp':
                    args['nocolortemp'] = True
                if key == 'help':  # make shift help because the docstring is overloaded above.
                    irc.reply("Options: --metric --alerts --forecast --almanac --pressure --wind --uv --visibility --dewpoint --astronomy --nocolortemp")
                    irc.reply("WeatherDB options: setweather <location> (set user's location). setmetric True/False (set metric option) setcolortemp True/False (display color temp?")
                    return

        # now that we're done with 'input things'
        # we need to decide on how to handle the location.
        # optinput = user specified location, regardless if they're known or not.
        # loc = the location that can come back if a user is known and this is set.
        # both of these might not be valid locations. however, if a user specifies a location, we should look it up.
        if optinput:  # if we have optinput, regardless if the user is known or not, autocomplete it.
            wloc = self._wuac(optinput)
            if not wloc:  # error looking up the location.
                irc.reply("ERROR: Sorry, I can not find a valid location for: {0}".format(optinput))
                return
        elif loc and not optinput:  # user is known. location is set. no optinput.
            wloc = loc   # set wloc as their location. worst case, the user gets an error for setting it wrong.
        else:  # no optinput. no location. error out. this should happen above but lets be redundant.
            irc.reply("ERROR: Sorry, you specify a city to search for weather.")
            return

        # build url now. first, apikey. then, iterate over urlArgs and insert.
        url = 'http://api.wunderground.com/api/%s/' % (self.APIKEY) # first part of url, w/APIKEY
        # now we need to set certain things for urlArgs based on args.
        for check in ['alerts', 'almanac', 'astronomy']:
            if args[check]: # if args['value'] is True, either via config or getopts.
                urlArgs['features'].append(check) # append to dict->key (list)
        # now, we use urlArgs dict to append to url.
        for (key, value) in urlArgs.items():
            if key == "features": # will always be at least conditions.
                url += "".join([item + '/' for item in value]) # listcmp the features/
            if key == "lang" or key == "bestfct" or key == "pws": # rest added with key:value
                url += "{0}:{1}/".format(key, value)

        # now that we're done, lets finally make our API call.
        page = self._wunderjson(url, wloc)
        if not page:
            irc.reply("ERROR: Failed to load Wunderground API. Check logs.")
            return

        # process json.
        try:
            data = json.loads(page.decode('utf-8'))
        except Exception as e:
            self.log.error("ERROR: could not process JSON from: {0} :: {1}".format(url, e))
            irc.reply("ERROR: Could not process JSON from Weather Underground. Check the logs.")
            return

        # now, a series of sanity checks before we process.
        if 'error' in data['response']:  # check if there are errors.
            errortype = data['response']['error']['type']  # type. description is below.
            errordesc = data['response']['error'].get('description', 'no description')
            irc.reply("ERROR: I got an error searching '{0}'. ({1}: {2})".format(loc, errortype, errordesc))
            return
        # if there is more than one city matching (Ambiguous Results).  we now go with the first (best?) match.
        # this should no longer be the case with our autocomplete routine above but we'll keep this anyways.
        if 'results' in data['response']:  # we grab the first location's "ZMW" which then gets constructed as location.
            first = 'zmw:%s' % data['response']['results'][0]['zmw']  # grab the "first" location and create the
            # grab this first location and search again.
            page = self._wunderjson(url, first)
            if not page:
                irc.reply("ERROR: Failed to load Wunderground API.")
                return
            # we're here if we got the second search (best?) now lets reload the json and continue.
            data = json.loads(page.decode('utf-8'))

        # no errors so we start the main part of processing.
        outdata = {}
        outdata['weather'] = data['current_observation']['weather']
        outdata['location'] = data['current_observation']['display_location']['full']
        outdata['humidity'] = data['current_observation']['relative_humidity']
        outdata['uv'] = data['current_observation']['UV']

        # handle wind. check if there is none first.
        if data['current_observation']['wind_mph'] < 1:  # no wind.
            outdata['wind'] = "None"
        else:  # we do have wind. process differently.
            if args['imperial']:  # imperial units for wind.
                outdata['wind'] = "{0}@{1}mph".format(self._wind(data['current_observation']['wind_degrees']), data['current_observation']['wind_mph'])
                if data['current_observation']['wind_gust_mph'] > 0:   # gusts?
                    outdata['wind'] += " ({0}mph gusts)".format(data['current_observation']['wind_gust_mph'])
            else:  # handle metric units for wind.
                outdata['wind'] = "{0}@{1}kph".format(self._wind(data['current_observation']['wind_degrees']),data['current_observation']['wind_kph'])
                if data['current_observation']['wind_gust_kph'] > 0:  # gusts?
                    outdata['wind'] += " ({0}kph gusts)".format(data['current_observation']['wind_gust_kph'])

        # handle the time. concept/method from WunderWeather plugin.
        observationTime = data['current_observation'].get('observation_epoch')
        localTime = data['current_observation'].get('local_epoch')
        # if we don't have the epoches from above, default to obs_time
        if not observationTime or not localTime:
            outdata['observation'] = data.get('observation_time', 'unknown').lstrip('Last Updated on ')
        else:  # we do have so format for relative time.
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

        # handle basics like temp/pressure/dewpoint. big conditional here
        # as we can display Imperial + Metric, or one or the other.
        if args['showImperialAndMetric']:
            # lets put C and F into strings to make it easier.
            tf = str(data['current_observation']['temp_f']) + 'F'
            tc = str(data['current_observation']['temp_c']) + 'C'
            outdata['temp'] = "{0}/{1}".format(self._tw(args['nocolortemp'], tf), self._tw(args['nocolortemp'], tc))
            # now lets do pressure.
            pin = str(data['current_observation']['pressure_in']) + 'in'
            pmb = str(data['current_observation']['pressure_mb']) + 'mb'
            outdata['pressure'] = "{0}/{1}".format(pin, pmb)
            # dewpoint.
            dpf = str(data['current_observation']['dewpoint_f']) + 'F'
            dpc = str(data['current_observation']['dewpoint_c']) + 'C'
            outdata['dewpoint'] = "{0}/{1}".format(self._tw(args['nocolortemp'], dpf), self._tw(args['nocolortemp'], dpc))
            # heatindex.
            hif = str(data['current_observation']['heat_index_f']) + 'F'
            hic = str(data['current_observation']['heat_index_c']) + 'C'
            outdata['heatindex'] = "{0}/{1}".format(self._tw(args['nocolortemp'], hif), self._tw(args['nocolortemp'], hic))
            # windchill.
            wcf = str(data['current_observation']['windchill_f']) + 'F'
            wcc = str(data['current_observation']['windchill_c']) + 'C'
            outdata['windchill'] = "{0}/{1}".format(self._tw(args['nocolortemp'], wcf), self._tw(args['nocolortemp'], wcc))
            # feels like
            flf = str(data['current_observation']['feelslike_f']) + 'F'
            flc = str(data['current_observation']['feelslike_c']) + 'C'
            outdata['feelslike'] = "{0}/{1}".format(self._tw(args['nocolortemp'], flf), self._tw(args['nocolortemp'], flc))
            # visibility.
            vmi = str(data['current_observation']['visibility_mi']) + 'mi'
            vkm = str(data['current_observation']['visibility_km']) + 'km'
            outdata['visibility'] = "{0}/{1}".format(vmi, vkm)
        else:  # don't display both (default)
            if args['imperial']:  # assigns the symbol based on metric.
                outdata['temp'] = self._tw(args['nocolortemp'], str(data['current_observation']['temp_f']) + 'F')
                outdata['pressure'] = str(data['current_observation']['pressure_in']) + 'in'
                outdata['dewpoint'] = self._tw(args['nocolortemp'], str(data['current_observation']['dewpoint_f']) + 'F')
                outdata['heatindex'] = self._tw(args['nocolortemp'], str(data['current_observation']['heat_index_f']) + 'F')
                outdata['windchill'] = self._tw(args['nocolortemp'], str(data['current_observation']['windchill_f']) + 'F')
                outdata['feelslike'] = self._tw(args['nocolortemp'], str(data['current_observation']['feelslike_f']) + 'F')
                outdata['visibility'] = str(data['current_observation']['visibility_mi']) + 'mi'
            else:  # metric.
                outdata['temp'] = self._tw(args['nocolortemp'], str(data['current_observation']['temp_c']) + 'C')
                outdata['pressure'] = str(data['current_observation']['pressure_mb']) + 'mb'
                outdata['dewpoint'] = self._tw(args['nocolortemp'], str(data['current_observation']['dewpoint_c']) + 'C')
                outdata['heatindex'] = self._tw(args['nocolortemp'], str(data['current_observation']['heat_index_c']) + 'C')
                outdata['windchill'] = self._tw(args['nocolortemp'], str(data['current_observation']['windchill_c']) + 'C')
                outdata['feelslike'] = self._tw(args['nocolortemp'], str(data['current_observation']['feelslike_c']) + 'C')
                outdata['visibility'] = str(data['current_observation']['visibility_km']) + 'km'
            
        # handle forecast data part. output will be below. (not --forecast)
        forecastdata = {}  # key = int(day), value = forecast dict.
        for forecastday in data['forecast']['txt_forecast']['forecastday']:
            tmpdict = {}
            tmpdict['day'] = forecastday['title']
            # tmpdict['symbol'] = self._weatherSymbol(forecastday['icon'])
            if args['imperial']:   # imperial.
                tmpdict['text'] = forecastday['fcttext']
            else:  # metric.
                tmpdict['text'] = forecastday['fcttext_metric']
            forecastdata[int(forecastday['period'])] = tmpdict

        # now this is the --forecast part.
        if args['forecast']:  # only if we get this in getopts.
            fullforecastdata = {}  # key = day (int), value = dict of forecast data.
            for forecastday in data['forecast']['simpleforecast']['forecastday']:
                tmpdict = {}
                tmpdict['day'] = forecastday['date']['weekday_short']
                tmpdict['symbol'] = self._weatherSymbol(forecastday['icon'])
                tmpdict['text'] = forecastday['conditions']
                if args['imperial']:  # imperial.
                    tmpdict['high'] = forecastday['high']['fahrenheit'] + "F"
                    tmpdict['low'] = forecastday['low']['fahrenheit'] + "F"
                else:  # metric.
                    tmpdict['high'] = forecastday['high']['celsius'] + "C"
                    tmpdict['low'] = forecastday['low']['celsius'] + "C"
                fullforecastdata[int(forecastday['period'])] = tmpdict

        # handle almanac
        if args['almanac']:
            outdata['highyear'] = data['almanac']['temp_high'].get('recordyear', 'NA')
            outdata['lowyear'] = data['almanac']['temp_low'].get('recordyear', 'NA')
            if args['imperial']:  # imperial.
                outdata['highnormal'] = data['almanac']['temp_high']['normal']['F'] + "F"
                outdata['lownormal'] = data['almanac']['temp_low']['normal']['F'] + "F"
                if outdata['highyear'] != "NA" and outdata['lowyear'] != "NA":
                    outdata['highrecord'] = data['almanac']['temp_high']['record']['F']
                    outdata['lowrecord'] = data['almanac']['temp_low']['record']['F']
                else:
                    outdata['highrecord'] = "NA"
                    outdata['lowrecord'] = "NA"
            else:  # metric.
                outdata['highnormal'] = data['almanac']['temp_high']['normal']['C'] + "C"
                outdata['lownormal'] = data['almanac']['temp_low']['normal']['C'] + "C"
                if outdata['highyear'] != "NA" and outdata['lowyear'] != "NA":
                    outdata['highrecord'] = data['almanac']['temp_high']['record']['C']
                    outdata['lowrecord'] = data['almanac']['temp_low']['record']['C']
                else:
                    outdata['highrecord'] = "NA"
                    outdata['lowrecord'] = "NA"

        # handle astronomy
        if args['astronomy']:
            outdata['moonilluminated'] = data['moon_phase']['percentIlluminated']
            outdata['moonage'] = data['moon_phase']['ageOfMoon']
            sunriseh = data['moon_phase']['sunrise']['hour']
            sunrisem = data['moon_phase']['sunrise']['minute']
            sunseth = data['moon_phase']['sunset']['hour']
            sunsetm = data['moon_phase']['sunset']['minute']
            outdata['sunrise'] = "{0}:{1}".format(sunriseh, sunrisem)  # construct sunrise.
            outdata['sunset'] = "{0}:{1}".format(sunseth, sunsetm)  # construct sunset. calc "time of day" below.
            outdata['lengthofday'] = "%dh%dm" % divmod((((int(sunseth)-int(sunriseh))+float((int(sunsetm)-int(sunrisem))/60.0))*60),60)

        # handle alerts
        if args['alerts']:  # only look for alerts if there.
            if data['alerts']:  # alerts is a list. it can also be empty.
                outdata['alerts'] = data['alerts'][0]['message']  # need to do some formatting below.
                outdata['alerts'] = outdata['alerts'].replace('\n', ' ')[:300]  # \n->' ' and max 300 chars.
                outdata['alerts'] = utils.str.normalizeWhitespace(outdata['alerts'])  # fix pesky double whitespacing.
            else:  # no alerts found (empty).
                outdata['alerts'] = "No alerts."

        # OUTPUT.
        # we go step-by-step to build the proper string. ° u" \u00B0C"
        output = "{0} :: {1} ::".format(self._bold(outdata['location'].encode('utf-8')), outdata['weather'].encode('utf-8'))
        # add in temperature.
        output += " {0}".format(outdata['temp'])
        # humidity.
        if args['humidity']:  # display humidity?
            output += " (Humidity: {0}) ".format(outdata['humidity'])
        else:
            output += " "
        # windchill/heatindex are conditional on season but test with startswith to see what to include
        if not outdata['windchill'].startswith("NA"):  # windchill.
            output += "| {0} {1} ".format(self._bold('Wind Chill:'), outdata['windchill'])
        if not outdata['heatindex'].startswith("NA"):  # heatindex.
            output += "| {0} {1} ".format(self._bold('Heat Index:'), outdata['heatindex'])
        # now get into the args dict for what to include (extras)
        for (k, v) in args.items():
            if k in ['wind', 'visibility', 'uv', 'pressure', 'dewpoint']: # if key is in extras
                if v: # if that key's value is True, we add it.
                    output += "| {0}: {1} ".format(self._bold(k.title()), outdata[k].encode('utf-8'))
        # add in the first two forecast item in conditions + updated time.
        output += "| {0}: {1}".format(self._bold(forecastdata[0]['day'].encode('utf-8')), forecastdata[0]['text'].encode('utf-8'))
        output += " {0}: {1}".format(self._bold(forecastdata[1]['day'].encode('utf-8')), forecastdata[1]['text'].encode('utf-8'))
         # show Updated?
        if args['updated']:
            output += " | {0} {1}".format(self._bold('Updated:'), outdata['observation'].encode('utf-8'))
        # finally, output the basic weather.
        irc.reply(output)

        # next, for outputting, handle the extras like alerts, almanac, astronomy, forecast.
        if args['alerts']:  # if --alerts issued.
            irc.reply("{0} :: {1}".format(self._bu("Alerts:"), outdata['alerts'].encode('utf-8')))
        # handle almanac if --almanac is given.
        if args['almanac']:
            if args['nocolortemp']:  # disable colored temp?
                output = "{0} :: Normal High: {1} (Record: {2} in {3}) | Normal Low: {4} (Record: {5} in {6})".format(\
                    self._bu('Almanac:'), outdata['highnormal'], outdata['highrecord'], outdata['highyear'],\
                    outdata['lownormal'], outdata['lowrecord'], outdata['lowyear'])
            else:  # colored temp.
                output = "{0} :: Normal High: {1} (Record: {2} in {3}) | Normal Low: {4} (Record: {5} in {6})".format(\
                    self._bu('Almanac:'), self._temp(outdata['highnormal']), self._temp(outdata['highrecord']),\
                    outdata['highyear'], self._temp(outdata['lownormal']), self._temp(outdata['lowrecord']), outdata['lowyear'])
            # now output to irc.
            irc.reply(output)
        # handle astronomy if --astronomy is given.
        if args['astronomy']:
            output = "{0} :: Moon illum: {1}%   Moon age: {2}d   Sunrise: {3}  Sunset: {4}  Length of Day: {5}".format(\
                self._bu('Astronomy:'), outdata['moonilluminated'], outdata['moonage'],outdata['sunrise'],\
                outdata['sunset'], outdata['lengthofday'])
            # irc output now.
            irc.reply(output)
        # handle main forecast if --forecast is given.
        if args['forecast']:
            outforecast = [] # prep string for output.
            for (k, v) in fullforecastdata.items(): # iterate through forecast data.
                if args['nocolortemp']:
                    outforecast.append("{0}: {1} ({2}/{3})".format(self._bold(v['day'].encode('utf-8')),\
                        v['text'].encode('utf-8'), v['high'], v['low']))
                else:
                    outforecast.append("{0}: {1} ({2}/{3})".format(self._bold(v['day'].encode('utf-8')),\
                        v['text'].encode('utf-8'), self._temp(v['high']), self._temp(v['low'])))
            # construct our string to output.
            output = "{0} :: {1}".format(self._bu('Forecast:'), " | ".join(outforecast))
            # now output to irc.
            irc.reply(output)

    wunderground = wrap(wunderground, [getopts({'alerts':'',
                                                'almanac':'',
                                                'astronomy':'',
                                                'forecast':'',
                                                'pressure':'',
                                                'wind':'',
                                                'uv':'',
                                                'visibility':'',
                                                'dewpoint':'',
                                                'humidity':'',
                                                'metric':'',
                                                'nocolortemp':'',
                                                'help':''}), optional('text')])

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
