# -*- coding: utf-8 -*-
###
# Copyright (c) 2012, spline
# All rights reserved.
#
#
###

# my libs
import urllib2
import json
import re
import math

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
# WeatherDB - to store a users nick, weather code (zip), and metric option
class WeatherDB(plugins.ChannelUserDB):
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
        regex = re.compile("\x1f|\x02|\x12|\x0f|\x16|\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
        return regex.sub('', string)
    
    # UNICODE
    def _unicode(string): # from pywunderground.
        """Try to convert a string to unicode using different encodings"""
        for encoding in ['utf-8', 'latin1']:
            try:
                result = unicode(string, encoding)
                return result
            except UnicodeDecodeError:
                pass
        result = unicode(string, 'utf-8', 'replace')
        return result
    
    # COLOR TEMPERATURE
    def temptest(self, irc, msg, args, opttemp):
        irc.reply("Temperature: {0}".format(self._temp(opttemp)))
    temptest = wrap(temptest, [('somethingWithoutSpaces')])

    def _temp(self, x):
        """Returns a colored string based on the temperature."""
        if x.endswith('C'):
            x = int((str(x).replace('C','')))*1.8+32
        else:
            x = int(str(x).replace('F',''))
        if x < 10:
            return ircutils.mircColor(x,'light blue')    
        if 10 <= x <= 32:
            return ircutils.mircColor(x,'blue')    
        if 32 <= x <= 49:
            return ircutils.mircColor(x,'teal')
        if 50 <= x <= 60:
            return ircutils.mircColor(x,'light green')   
        if 61 <= x <= 70:
            return ircutils.mircColor(x,'green')   
        if 71 <= x <= 80:
            return ircutils.mircColor(x,'yellow')   
        if 81 <= x <= 90:
            return ircutils.mircColor(x,'orange')   
        if x > 90:
            return ircutils.mircColor(x,'red')

    # DEGREES TO DIRECTION (wind)
    def _normalize_angle(self, angle):
	    """ Takes angle in degrees and returns angle from 0 to 360 degrees """
	    cycles = angle/360.
	    normalized_cycles = angle/360. - math.floor(cycles)*360.
	    return normalized_cycles*360.
  
    def _wind(self, angle):
        direction_names = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
        directions_num = len(direction_names)
        directions_step = 360./directions_num
        index = int(round((angle/360. - math.floor(angle/360.)*360.)/directions_step))
        #index = int(round( _normalize_angle(angle)/directions_step ))
        index %= directions_num
        return direction_names[index]
    
    def _winddir(self, degrees):
        """ Convert wind degrees to direction """
        try:
            degrees = int(degrees)
        except ValueError:
            return degrees
        if degrees < 23 or degrees >= 338:
            return 'N'
        elif degrees < 68:
            return 'NE'
        elif degrees < 113:
            return 'E'
        elif degrees < 158:
            return 'SE'
        elif degrees < 203:
            return 'S'
        elif degrees < 248:
            return 'SW'
        elif degrees < 293:
            return 'W'
        elif degrees < 338:
            return 'NW'
    
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
        self.db.setId(msg.nick, optid)
        irc.reply("I have changed {0}'s weather ID to {1}".format(msg.nick, optid))
    setweather = wrap(setweather, [('somethingWithoutSpaces')])
           
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
       
    # CHECK FOR API KEY.  
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
                'forecastDays':self.registryValue('forecastDays'),
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
        url += 'q/%s.json' % (optinput.replace(' ','')) # remove spaces.

        self.log.info(url)
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
            if data['current_observation']['wind_mph'] is 0: # no wind.
                outdata['wind'] = "No wind."
            else:
                outdata['wind'] = "{0}@{1}mph".format(self._wind(data['current_observation']['wind_degrees']),data['current_observation']['wind_mph'])
            if data['current_observation']['wind_gust_mph'] is not 0:
                outdata['wind'] += " ({0}mph gusts)".format(data['current_observation']['wind_gust_mph'])
        else:
            if data['current_observation']['wind_kph'] is 0: # no wind.
                outdata['wind'] = "No wind."
            else:
                outdata['wind'] = "{0}@{1}kph".format(self._wind(data['current_observation']['wind_degrees']),data['current_observation']['wind_mph'])
            if data['current_observation']['wind_gust_mph'] is not 0:
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
            outdata['temp'] = str(data['current_observation']['temp_f']) + 'F'#+ u'\xb0F'
            outdata['pressure'] = data['current_observation']['pressure_mb']
            outdata['dewpoint'] = str(data['current_observation']['dewpoint_f']) + 'F'
            outdata['heatindex'] = str(data['current_observation']['heat_index_f']) + 'F'
            outdata['windchill'] = str(data['current_observation']['windchill_f']) + 'F'
            outdata['feelslike'] = str(data['current_observation']['feelslike_f']) + 'F'
            outdata['visibility'] = str(data['current_observation']['visibility_mi']) + 'mi'
        else:
            outdata['temp'] = str(data['current_observation']['temp_c']) + 'C'#+ u'\xb0C'
            outdata['pressure'] = data['current_observation']['pressure_in']
            outdata['dewpoint'] = str(data['current_observation']['dewpoint_c']) + 'C'
            outdata['heatindex'] = str(data['current_observation']['heat_index_c']) + 'C'
            outdata['windchill'] = str(data['windchill_c']) + 'C'
            outdata['feelslike'] = str(data['current_observation']['feelslike_c']) + 'C'
            outdata['visibility'] = str(data['current_observation']['visibility_km']) + 'km'
        
        # handle forecast data part. output will be below.
        # this is not the --forecast part.
        forecastdata = {} # dict to store data in.
        for forecastday in data['forecast']['txt_forecast']['forecastday']:
            tmpdict = {}
            tmpdict['day'] = forecastday['title']
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
                tmpdict['text'] = forecastday['conditions']
                if args['imperial']: # check for metric.
                    tmpdict['high'] = forecastday['high']['fahrenheit'] 
                    tmpdict['low'] = forecastday['low']['fahrenheit']
                else:
                    tmpdict['high'] = forecastday['high']['celsius'] 
                    tmpdict['low'] = forecastday['low']['celsius']                
                fullforecastdata[int(forecastday['period'])] = tmpdict

        # handle almanac
        if args['almanac']:
            outdata['highyear'] = data['almanac']['temp_high']['recordyear']
            outdata['lowyear'] = data['almanac']['temp_low']['recordyear']
            if args['imperial']:
                outdata['highnormal'] = data['almanac']['temp_high']['normal']['F']
                outdata['highrecord'] = data['almanac']['temp_high']['record']['F']
                outdata['lownormal'] = data['almanac']['temp_low']['normal']['F']
                outdata['lowrecord'] = data['almanac']['temp_low']['record']['F']
            else:
                outdata['highnormal'] = data['almanac']['temp_high']['normal']['C']
                outdata['highrecord'] = data['almanac']['temp_high']['record']['C']
                outdata['lownormal'] = data['almanac']['temp_low']['normal']['C']
                outdata['lowrecord'] = data['almanac']['temp_low']['record']['C']

        # handle astronomy
        if args['astronomy']:
            outdata['moonilluminated'] = data['moon_phase']['percentIlluminated']
            outdata['moonage'] = data['moon_phase']['ageOfMoon']
            outdata['sunrise'] = "{0}:{1}".format(data['moon_phase']['sunrise']['hour'],data['moon_phase']['sunrise']['minute'])
            outdata['sunset'] = "{0}:{1}".format(data['moon_phase']['sunset']['hour'],data['moon_phase']['sunset']['minute'])
        
        # handle alerts
        if args['alerts']:
            if data.has_key('alerts'):
                outdata['alerts'] = data['alerts'][:300] # alert limit to 300.
            else:
                outdata['alerts'] = "No alerts."
                
        # OUTPUT
        # now, build output object with what to output.       
        output = "Weather for {0} :: {1}° (Feels like: {2}) | {3} {4}".format(\
            self._bold(outdata['location']),self._temp(outdata['temp']),self._temp(outdata['feelslike']),\
                self._bold('Conditions:'), outdata['weather'])
        # windchill/heatindex are conditional on season but test with startswith to see what to include
        if not outdata['windchill'].startswith("NA"): 
            output += " | {0} {1}".format(self._bold('Wind Chill:'), outdata['windchill'])
        if not outdata['heatindex'].startswith("NA"): 
            output += " | {0} {1}".format(self._bold('Heat Index:'), outdata['heatindex'])
        # now get into the args dict for what to include (extras)
        extras = ['wind','visibility','uv','pressure','dewpoint']
        for (k,v) in args.items():
            if k in extras: # if key is in extras
                if v: # if that key's value is True
                    output += " | {0}: {1}".format(self._bold(k.title()), outdata[k])
        # add in the first forecast item in conditions.
        output += " | {0} {1}".format(self._bold(forecastdata[0]['day']),forecastdata[0]['text'])
        # finally, add the time and output.
        output += " | {0} {1}".format(self._bold('Updated:'), outdata['observation'])
        
        if self.registryValue('disableANSI', msg.args[0]):
            irc.reply(self._strip(output))
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
            output = "{0} :: {1} {2} {3} {4} {5} {6}".format(self._bold('Almanac:'),\
                outdata['highnormal'],outdata['highrecord'],outdata['highyear'],\
                    outdata['lownormal'],outdata['lowrecord'],outdata['lowyear'])
            if self.registryValue('disableANSI', msg.args[0]):
                irc.reply(self._strip(output))
            else:
                irc.reply(output)              
                                    
        # handle main forecast if --forecast is given.
        if args['forecast']:
            outforecast = [] # prep string for output.
            for (k,v) in fullforecastdata.items(): # iterate through forecast data.
                outforecast.append("{0}: {1} ({2}/{3})".format(self._bold(v['day']),v['text'],v['high'],v['low']))
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
