# -*- coding: utf-8 -*-
###
# Copyright (c) 2012-2013, spline
# All rights reserved.
###

# my libs
import urllib2
import json
import re
from math import floor
from urllib import quote

# extra supybot libs
import supybot.conf as conf
import supybot.ircdb as ircdb
import supybot.world as world

# supybot libs
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Weather')

@internationalizeDocstring
class WeatherDB(plugins.ChannelUserDB):
    """WeatherDB class to store our users locations and metric."""
    def __init__(self, *args, **kwargs):
        plugins.ChannelUserDB.__init__(self, *args, **kwargs)

    def serialize(self, v):
        return list(v)

    def deserialize(self, channel, id, L):
        (id, metric) = L
        return (id, metric)

    def getId(self, nick):
        return self['x', nick.lower()][0]

    def getMetric(self, nick):
        return self['x', nick.lower()][1]

    def setId(self, nick, id):
        try:
            metric = self['x', nick.lower()][1]
        except KeyError:
            metric = 'False'
        self['x', nick.lower()] = (id, metric,)

    def setMetric(self, nick, metric):
        try:
            id = self['x', nick.lower()][0]
        except:
            id = '10121'
        self['x', nick.lower()] = (id, metric,)

class Weather(callbacks.Plugin):
    """Add the help for "@plugin help Weather" here
    This should describe *how* to use this plugin."""
    threaded = True

    # BASICS/WeatherDB
    def __init__(self, irc):
        self.__parent = super(Weather, self)
        self.__parent.__init__(irc)
        self.db = WeatherDB(dbfilename)
        self.APIKEY = self.registryValue('apiKey')
        world.flushers.append(self.db.flush)

    def die(self):
        if self.db.flush in world.flushers:
            world.flushers.remove(self.db.flush)
        self.db.close()
        self.__parent.die()

    # COLORING
    def _bold(self, string):
        return ircutils.bold(string)

    def _bu(self, string):
        return ircutils.underline(ircutils.bold(string))

    def _blue(self, string):
        return ircutils.mircColor(string, 'blue')

    def _red(self, string):
        return ircutils.mircColor(string, 'red')

    def _strip(self, string): # from http://bit.ly/X0vm6K
        #regex = re.compile("\x1f|\x02|\x12|\x0f|\x16|\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
        #return regex.sub('', string)
        return ircutils.stripFormatting(string)

    # WEATHER SYMBOLS
    def _weatherSymbol(self, code):
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
                 'chancetstorms':'?☔',
                 'unknown':''}
        try:
            return table[code]
        except KeyError:
            return None

    # COLOR TEMPERATURE
    def _temp(self, x):
        """Returns a colored string based on the temperature."""
        if x.endswith('C'):
            x = float(str(x).replace('C','')) * 9 / 5 + 32
            unit = "C"
        else:
            x = float(str(x).replace('F',''))
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
        if unit == "F":
            return ircutils.mircColor(("{0:.0f}F".format(x)),color)
        else:
            return ircutils.mircColor(("{0:.0f}C".format((x - 32) * 5 / 9)),color)

    # DEGREES TO DIRECTION (wind)
    def _wind(self, angle, useSymbols=False):
        if not useSymbols:
            direction_names = ["N","NE","E","SE","S","SW","W","NW"]
        else:
            direction_names = ['↑','↗','→','↘','↓','↙','←','↖']
        directions_num = len(direction_names)
        directions_step = 360./directions_num
        index = int(round((angle/360. - floor(angle/360.)*360.)/directions_step))
        index %= directions_num
        return direction_names[index]

    # PUBLIC FUNCTIONS TO WORK WITH WEATHERDB.
    def weatherusers(self, irc, msg, args):
        """
        Returns the amount of users we know about.
        """
        output = str(len(self.db.keys()))
        irc.reply("I know about {0} users in my weather database.".format(str(output)))
    weatherusers = wrap(weatherusers)

    def setmetric(self, irc, msg, args, optboolean):
        """<True|False>
        Sets the user's use metric setting to True or False.
        If True, will use netric. If False, will use imperial.
        """
        # first, title case and cleanup as helper. Still must be True or False.
        optboolean = optboolean.title().strip() # partial helpers.
        if optboolean != "True" and optboolean != "False":
            irc.reply("metric setting must be True or False")
            return
        # now, test if we have a username. setmetric for an unknown username = error
        try:
            self.db.getId(msg.nick)
        except KeyError:
            irc.reply("I have no user in the DB named {0}. Try setweather first.".format(msg.nick))
            return
        # now change it.
        self.db.setMetric(msg.nick, optboolean)
        irc.reply("I have changed {0}'s metric setting to {1}".format(msg.nick, optboolean))
    setmetric = wrap(setmetric, [('somethingWithoutSpaces')])

    def setweather(self, irc, msg, args, optid):
        """<location code>
        Set's weather location code for your nick as <location code>.
        Use your zip/postal code to keep it simple. Ex: setweather 03062
        """
        # set the weather id based on nick.
        optid = optid.replace(' ','')
        self.db.setId(msg.nick, optid)
        irc.reply("I have changed {0}'s weather ID to {1}".format(msg.nick, optid))
    setweather = wrap(setweather, [('text')])

    def getmetric(self, irc, msg, args, optnick):
        """[nick]
        Get the metric setting of your or [nick].
        """
        # allows us to specify the nick.
        if not optnick:
            optnick = msg.nick
        # now try to fetch the metric. Tests if we have a username.
        try:
            irc.reply("The metric setting for {0} is {1}".format(optnick, self.db.getMetric(optnick)))
        except KeyError:
            irc.reply('I have no weather metric setting for {0}'.format(optnick))
    getmetric = wrap(getmetric, [optional('somethingWithoutSpaces')])

    def getweather(self, irc, msg, args, optnick):
        """[nick]
        Get the weather ID of your or [nick].
        """
        # allow us to specify the nick if we don't have it.
        if not optnick:
            optnick = msg.nick
        # now try and fetch the metric setting. error if it's broken.
        try:
            irc.reply("The weather ID for {0} is {1}".format(optnick, self.db.getId(optnick)))
        except KeyError:
            irc.reply('I have no weather ID for %s.' % optnick)
    getweather = wrap(getweather, [optional('somethingWithoutSpaces')])

    # CHECK FOR API KEY. (NOT PUBLIC)
    def keycheck(self, irc):
        """Check and make sure we have an API key."""
        if len(self.APIKEY) < 1 or not self.APIKEY or self.APIKEY == "Not set":
            irc.reply("ERROR: Need an API key. config plugins.Weather.apiKey apiKey .")
            return False
        else:
            return True

    ####################
    # PUBLIC FUNCTIONS #
    ####################

    def wunderground(self, irc, msg, args, optlist, optinput):
        """[--options] [location]
        Location must be one of: US state/city (CA/San_Francisco), zipcode, country/city (Australia/Sydney), airport code (KJFK)
        For options:
        """
        # first, check if we have an API key. Useless w/o this.
        if not self.keycheck(irc):
            return False

        # urlargs will be used to build the url to query the API.
        urlArgs = {'features':['conditions','forecast'],
                   'lang':self.registryValue('lang'),
                   'bestfct':'1',
                   'pws':'0'
                  }
        # now, start our dict for output formatting.
        args = {'imperial':self.registryValue('useImperial', msg.args[0]),
                'alerts':self.registryValue('alerts'),
                'almanac':self.registryValue('almanac'),
                'astronomy':self.registryValue('astronomy'),
                'pressure':self.registryValue('showPressure'),
                'wind':self.registryValue('showWind'),
                'forecast':False,
                'strip':False,
                'uv':False,
                'visibility':False,
                'dewpoint':False
               }

        # now check if we have a location. if no location, use the userdb. also set for metric variable.
        # autoip.json?geo_ip=38.102.136.138
        if not optinput:
            try:
                optinput = self.db.getId(msg.nick)
                optmetric = self.db.getMetric(msg.nick) # set our imperial units here.
                if optmetric == "True":
                    args['imperial'] = False
                else:
                    args['imperial'] = True
            except KeyError:
                irc.reply("I did not find a preset location for you. Set via: setweather location or specify a location")
                return

        # handle optlist (getopts). this will manipulate output via args dict.
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

        # build url now. first, apikey. then, iterate over urlArgs and insert.
        # urlArgs['features'] also manipulated via what's in args.
        url = 'http://api.wunderground.com/api/%s/' % (self.APIKEY) # first part of url, w/APIKEY
        # now we need to set certain things for urlArgs based on args.
        for check in ['alerts','almanac','astronomy']:
            if args[check]: # if args['value'] is True, either via config or getopts.
                urlArgs['features'].append(check) # append to dict->key (list)
        # now, we use urlArgs dict to append to url.
        for (key, value) in urlArgs.items():
            if key == "features": # will always be at least conditions.
                url += "".join([item + '/' for item in value]) # listcmp the features/
            if key == "lang" or key == "bestfct" or key == "pws": # rest added with key:value
                url += "{0}:{1}/".format(key, value)
        # finally, attach the q/input. url is now done.
        url += 'q/%s.json' % quote(optinput)

        #self.log.info(url)
        # try and query.
        try:
            request = urllib2.Request(url)
            u = urllib2.urlopen(request)
        except Exception as e:
            self.log.info("Error loading {0} message {1}".format(url, e))
            irc.reply("Failed to load wunderground API: %s" % e)
            return

        # process the json, check (in orders) for errors, multiple results, and one last
        # sanity check. then we can process it.
        data = json.load(u)

        # check if we got errors and return.
        if 'error' in data['response']:
            errortype = data['response']['error']['type']
            errordesc = data['response']['error'].get('description', 'no description')
            irc.reply("{0} I got an error searching for {1}. ({2}: {3})".format(self._red("ERROR:"), optinput, errortype, errordesc))
            return

        # if there is more than one city matching.
        if 'results' in data['response']:
            output = [item['city'] + ", " + item['state'] + " (" + item['country_name'] + ")" for item in data['response']['results']]
            irc.reply("More than 1 city matched your query, try being more specific: {0}".format(" | ".join(output)))
            return

        # last sanity check
        if not data.has_key('current_observation'):
            irc.reply("{0} something went horribly wrong looking up weather for {1}. Contact the plugin owner.".format(self._red("ERROR:"), optinput))
            return

        # done with error checking.
        # now, put everything into outdata dict for output later.
        outdata = {}
        outdata['weather'] = data['current_observation']['weather']
        outdata['location'] = data['current_observation']['display_location']['full']
        outdata['humidity'] = data['current_observation']['relative_humidity']
        outdata['uv'] = data['current_observation']['UV']

        # handle wind. check if there is none first.
        if args['imperial']:
            if data['current_observation']['wind_mph'] < 1: # no wind.
                outdata['wind'] = "None"
            else:
                outdata['wind'] = "{0}@{1}mph".format(self._wind(data['current_observation']['wind_degrees']),data['current_observation']['wind_mph'])
            if data['current_observation']['wind_gust_mph'] > 0:
                outdata['wind'] += " ({0}mph gusts)".format(data['current_observation']['wind_gust_mph'])
        else:
            if data['current_observation']['wind_kph'] < 1: # no wind.
                outdata['wind'] = "None"
            else:
                outdata['wind'] = "{0}@{1}kph".format(self._wind(data['current_observation']['wind_degrees']),data['current_observation']['wind_mph'])
            if data['current_observation']['wind_gust_mph'] > 0:
                outdata['wind'] += " ({0}kph gusts)".format(data['current_observation']['wind_gust_kph'])

        # handle the time. concept/method from WunderWeather plugin.
        observationTime = data['current_observation'].get('observation_epoch', None)
        localTime = data['current_observation'].get('local_epoch', None)
        if not observationTime or not localTime: # if we don't have the epoches from above, default to obs_time
            outdata['observation'] = data.get('observation_time', 'unknown').lstrip('Last Updated on ')
        else: # format for relative time.
            s = int(localTime) - int(observationTime)
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

        # all conditionals for imperial/metric
        if args['imperial']:
            outdata['temp'] = str(data['current_observation']['temp_f']) + 'F'
            outdata['pressure'] = data['current_observation']['pressure_in'] + 'in'
            outdata['dewpoint'] = str(data['current_observation']['dewpoint_f']) + 'F'
            outdata['heatindex'] = str(data['current_observation']['heat_index_f']) + 'F'
            outdata['windchill'] = str(data['current_observation']['windchill_f']) + 'F'
            outdata['feelslike'] = str(data['current_observation']['feelslike_f']) + 'F'
            outdata['visibility'] = str(data['current_observation']['visibility_mi']) + 'mi'
        else:
            outdata['temp'] = str(data['current_observation']['temp_c']) + 'C'
            outdata['pressure'] = data['current_observation']['pressure_mb'] + 'mb'
            outdata['dewpoint'] = str(data['current_observation']['dewpoint_c']) + 'C'
            outdata['heatindex'] = str(data['current_observation']['heat_index_c']) + 'C'
            outdata['windchill'] = str(data['current_observation']['windchill_c']) + 'C'
            outdata['feelslike'] = str(data['current_observation']['feelslike_c']) + 'C'
            outdata['visibility'] = str(data['current_observation']['visibility_km']) + 'km'

        # handle forecast data part. output will be below.
        # this is not the --forecast part.
        forecastdata = {} # dict to store data in.
        for forecastday in data['forecast']['txt_forecast']['forecastday']:
            tmpdict = {}
            tmpdict['day'] = forecastday['title']
            tmpdict['symbol'] = forecastday['icon'] # partlycloudy
            if args['imperial']:
                tmpdict['text'] = forecastday['fcttext']
            else:
                tmpdict['text'] = forecastday['fcttext_metric']
            forecastdata[int(forecastday['period'])] = tmpdict

        # now this is the --forecast part.
        if args['forecast']:
            fullforecastdata = {}
            for forecastday in data['forecast']['simpleforecast']['forecastday']:
                tmpdict = {}
                tmpdict['day'] = forecastday['date']['weekday_short']
                tmpdict['symbol'] = forecastday['icon'] # partlycloudy
                tmpdict['text'] = forecastday['conditions']
                if args['imperial']: # check for metric.
                    tmpdict['high'] = forecastday['high']['fahrenheit'] + "F"
                    tmpdict['low'] = forecastday['low']['fahrenheit'] + "F"
                else:
                    tmpdict['high'] = forecastday['high']['celsius'] + "C"
                    tmpdict['low'] = forecastday['low']['celsius'] + "C"
                fullforecastdata[int(forecastday['period'])] = tmpdict

        # handle almanac
        if args['almanac']:
            outdata['highyear'] = data['almanac']['temp_high']['recordyear']
            outdata['lowyear'] = data['almanac']['temp_low']['recordyear']
            if args['imperial']:
                outdata['highnormal'] = data['almanac']['temp_high']['normal']['F'] + "F"
                outdata['highrecord'] = data['almanac']['temp_high']['record']['F'] + "F"
                outdata['lownormal'] = data['almanac']['temp_low']['normal']['F'] + "F"
                outdata['lowrecord'] = data['almanac']['temp_low']['record']['F'] + "F"
            else:
                outdata['highnormal'] = data['almanac']['temp_high']['normal']['C'] + "C"
                outdata['highrecord'] = data['almanac']['temp_high']['record']['C'] + "C"
                outdata['lownormal'] = data['almanac']['temp_low']['normal']['C'] + "C"
                outdata['lowrecord'] = data['almanac']['temp_low']['record']['C'] + "C"

        # handle astronomy
        if args['astronomy']:
            outdata['moonilluminated'] = data['moon_phase']['percentIlluminated']
            outdata['moonage'] = data['moon_phase']['ageOfMoon']
            sunriseh = int(data['moon_phase']['sunrise']['hour'])
            sunrisem = int(data['moon_phase']['sunrise']['minute'])
            sunseth = int(data['moon_phase']['sunset']['hour'])
            sunsetm = int(data['moon_phase']['sunset']['minute'])
            outdata['sunrise'] = "{0}:{1}".format(sunriseh,sunrisem)
            outdata['sunset'] = "{0}:{1}".format(sunseth,sunsetm)
            outdata['lengthofday'] = "%dh%dm" % divmod((((sunseth-sunriseh)+float((sunsetm-sunrisem)/60.0))*60),60)

        # handle alerts
        if args['alerts']:
            if data['alerts']:
                outdata['alerts'] = data['alerts'][:300] # alert limit to 300.
            else:
                outdata['alerts'] = "No alerts."

        # OUTPUT
        # now, build output object with what to output. ° u" \u00B0C"
        if self.registryValue('disableColoredTemp'):
            output = "Weather for {0} :: {1} ({2})".format(self._bold(outdata['location']),\
                outdata['weather'],outdata['temp'])
        else:
            output = "Weather for {0} :: {1} ({2})".format(self._bold(outdata['location']),\
                outdata['weather'],self._temp(outdata['temp']))
        # windchill/heatindex are conditional on season but test with startswith to see what to include
        if not outdata['windchill'].startswith("NA"):
            if self.registryValue('disableColoredTemp'):
                output += " | {0} {1}".format(self._bold('Wind Chill:'), outdata['windchill'])
            else:
                output += " | {0} {1}".format(self._bold('Wind Chill:'), self._temp(outdata['windchill']))
        if not outdata['heatindex'].startswith("NA"):
            if self.registryValue('disableColoredTemp'):
                output += " | {0} {1}".format(self._bold('Heat Index:'), outdata['heatindex'])
            else:
                output += " | {0} {1}".format(self._bold('Heat Index:'), self._temp(outdata['heatindex']))
        # now get into the args dict for what to include (extras)
        for (k,v) in args.items():
            if k in ['wind','visibility','uv','pressure','dewpoint']: # if key is in extras
                if v: # if that key's value is True
                    output += " | {0}: {1}".format(self._bold(k.title()), outdata[k])
        # add in the first forecast item in conditions + updated time.
        output += " | {0}: {1} {2}: {3}".format(self._bold(forecastdata[0]['day']),\
            forecastdata[0]['text'],self._bold(forecastdata[1]['day']),forecastdata[1]['text'])
        output += " | {0} {1}".format(self._bold('Updated:'), outdata['observation'])
        # output.
        if self.registryValue('disableANSI', msg.args[0]):
            irc.reply(ircutils.stripFormatting(output))
        else:
            irc.reply(output)

        # next, for outputting, handle the extras like alerts, almanac, etc.
        if args['alerts']:
            output = "{0} :: {1}".format(self._bu("Alerts:"),outdata['alerts'])
            if self.registryValue('disableANSI', msg.args[0]):
                irc.reply(self._strip(output))
            else:
                irc.reply(output)
        # handle almanac
        if args['almanac']:
            if self.registryValue('disableColoredTemp'):
                output = "{0} :: Normal High: {1} (Record: {2} in {3}) | Normal Low: {4} (Record: {5} in {6})".format(\
                    self._bu('Almanac:'),outdata['highnormal'],outdata['highrecord'],\
                        outdata['highyear'],outdata['lownormal'],outdata['lowrecord'],outdata['lowyear'])
            else:
                output = "{0} :: Normal High: {1} (Record: {2} in {3}) | Normal Low: {4} (Record: {5} in {6})".format(\
                    self._bu('Almanac:'),self._temp(outdata['highnormal']),self._temp(outdata['highrecord']),\
                        outdata['highyear'],self._temp(outdata['lownormal']),self._temp(outdata['lowrecord']),outdata['lowyear'])
            if self.registryValue('disableANSI', msg.args[0]):
                irc.reply(self._strip(output))
            else:
                irc.reply(output)
        # handle astronomy
        if args['astronomy']:
            output = "{0} Moon illum: {1}%   Moon age: {2}d   Sunrise: {3}  Sunset: {4}  Length of Day: {5}".format(self._bu('Astronomy:'),outdata['moonilluminated'],\
                outdata['moonage'],outdata['sunrise'],outdata['sunset'], outdata['lengthofday'])
            if self.registryValue('disableANSI', msg.args[0]):
                irc.reply(self._strip(output))
            else:
                irc.reply(output)
        # handle main forecast if --forecast is given.
        if args['forecast']:
            outforecast = [] # prep string for output.
            for (k,v) in fullforecastdata.items(): # iterate through forecast data.
                if self.registryValue('disableColoredTemp'):
                    outforecast.append("{0}: {1} ({2}/{3})".format(self._bold(v['day']),v['text'],\
                        v['high'],v['low']))
                else:
                    outforecast.append("{0}: {1} ({2}/{3})".format(self._bold(v['day']),v['text'],\
                        self._temp(v['high']),self._temp(v['low'])))
            output = "{0} :: {1}".format(self._bu('Forecast:'), " | ".join(outforecast)) # string to output
            if self.registryValue('disableANSI', msg.args[0]):
                irc.reply(self._strip(output))
            else:
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
                                                'metric':''}), optional('text')])

dbfilename = conf.supybot.directories.data.dirize("Weather.db")

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
