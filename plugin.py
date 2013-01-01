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
        
    # FORMATTING
    def _bold(self, string):
        return ircutils.bold(string)

    def _blue(self, string):
        return ircutils.mircColor(string, 'blue')

    def _bu(self, string):
        return ircutils.underline(ircutils.bold(string))

    def _red(self, string):
        return ircutils.mircColor(string, 'red')

    def _temp(self, x):
        """Returns a colored string based on the temperature."""
        if x.endswith('C'):
            x = x.replace('C','')
            x = int([x*1.8+32,(x-32)/1.8])
        else:
            x = int(x.replace('F',''))
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
        Use your zipcode to keep it simple. Ex: setweather 03062
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
                'uv':False,
                'visibility':False,
                'dewpoint':False
               }
        
        # now check if we have a location. if no location, use the userdb. also set for metric variable.
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
            # autoip.json?geo_ip=38.102.136.138
                
        # handle optlist (getopts). this will manipulate output via args dict.
        if optlist:
            for (key, value) in optlist:
                if key == "metric":
                    args['imperial'] = False
                if key == 'alerts':
                    args['alerts'] = True
                if key == 'days':
                    args['forecastDays'] = value
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
        
        # build url now. first, apikey. then, iterate over urlArgs and insert.
        # urlArgs['features'] also manipulated via what's in args.
        url = 'http://api.wunderground.com/api/%s/' % (self.APIKEY) # first part of url, w/APIKEY
        # now we need to set certain things for urlArgs based on args.
        for check in ['alerts','almanac']:
            if args[check]: # if args['value'] is True, either via config or getopts.
                urlArgs['features'].append(check) # append to dict->key (list)
        # now, we use urlArgs dict to append to url.
        for (key, value) in urlArgs.items(): 
            if key == "features": # will always be at least conditions.
                url += "".join([item + '/' for item in value]) # listcmp the features/
            if key == "lang" or key == "bestfct" or key == "pws": # rest added with key:value
                url += "{0}:{1}/".format(key, value)
        # finally, attach the q/input.
        url += 'q/%s.json' % (optinput)

        self.log.info(url)
        # try and query.                        
        try: 
            request = urllib2.Request(url)
            u = urllib2.urlopen(request)
        except Exception as e:
            self.log.info("Error loading {0} message {1}".format(url, e))
            irc.reply("Failed to load wunderground API: %s" % e)
            return
        
        # process the json.
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
        
        # now, put everything into outdata dict for output later.
        outdata = {}

        # basics for weather output.        
        outdata['weather'] = data['current_observation']['weather']
        outdata['location'] = data['current_observation']['display_location']['full']
        outdata['humidity'] = data['current_observation']['relative_humidity']
        outdata['uv'] = data['current_observation']['UV']
        
        # handle wind. check if there is none first.
        if args['imperial']:
            if data['current_observation']['wind_mph'] is 0: # no wind.
                outdata['wind'] = "No wind."
            else:
                outdata['wind'] = "{0} at {1}mph.".format(data['current_observation']['wind_dir'],data['current_observation']['wind_mph'])
            if data['current_observation']['wind_gust_mph'] is not 0:
                outdata['wind'] += " Gusts to {0}mph".format(data['current_observation']['wind_gust_mph'])
        else:
            if data['current_observation']['wind_kph'] is 0: # no wind.
                outdata['wind'] = "No wind."
            else:
                outdata['wind'] = "{0} at {1}kph.".format(data['current_observation']['wind_dir'],data['current_observation']['wind_kph'])
            if data['current_observation']['wind_gust_mph'] is not 0:
                outdata['wind'] += " Gusts to {0}kph".format(data['current_observation']['wind_gust_kph'])
            
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
                outdata['observation'] = '{0} seconds ago'.format(s)
            elif s < 120:
                outdata['observation'] = '1 minute ago'
            elif s < 3600:
                outdata['observation'] = '{0} minutes ago'.format(s/60)
            elif s < 7200:
                outdata['observation'] = '1 hour ago'
            else:
                outdata['observation'] = '{0} hours ago'.format(s/3600)
        
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
        forecastdata = {} # dict to store data in.
        for forecastday in data['forecast']['txt_forecast']['forecastday']:
            tmpdict = {}
            tmpdict['day'] = forecastday['title']
            if args['imperial']: 
                tmpdict['text'] = forecastday['fcttext']
            else:
                tmpdict['text'] = forecastday['fcttext_metric']
            forecastdata[int(forecastday['period'])] = tmpdict
        
        # now, build output object with what to output.       
        output = "Weather for {0} :: {1} (Feels like: {2}) | {3} {4}".format(\
            self._bold(outdata['location']),self._temp(outdata['temp']),self._temp(outdata['feelslike']),\
                self._bold('Conditions:'), outdata['weather'])
            
        # windchill/heatindex are conditional on season but test with startswith to see what to include
        if not outdata['windchill'].startswith("NA"): # conditional for windchill
            output += " | {0} {1}".format(self._bold('Wind Chill:'), outdata['windchill'])
        if not outdata['heatindex'].startswith("NA"): # conditional for heatindex
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
        irc.reply(output.encode('utf-8'))
        
        # next, handle the extras like alerts, almanac, etc.
        # handle if we're looking for alerts
        if args['alerts']:
            if data.has_key('alerts'):
                if data['alerts']:
                    irc.reply("{0} :: {1}".format(self._bu("Alerts:"),data['alerts']))
            

        # handle almanac
        if args['almanac']:
            if data.has_key('almanac'):
                if args['imperial']: # grab the data in almanac.
                    temphighnormal = data['almanac']['temp_high']['normal']['F']
                    temphighrecord = data['almanac']['temp_high']['record']['F']
                    temphighyear = data['almanac']['temp_high']['recordyear']
                    templownormal = data['almanac']['temp_low']['normal']['F']
                    templowrecord = data['almanac']['temp_low']['record']['F']
                    templowyear = data['almanac']['temp_low']['recordyear']
                else:
                    temphighnormal = data['almanac']['temp_high']['normal']['C']
                    temphighrecord = data['almanac']['temp_high']['record']['C']
                    temphighyear = data['almanac']['temp_high']['recordyear']
                    templownormal = data['almanac']['temp_low']['normal']['C']
                    templowrecord = data['almanac']['temp_low']['record']['C']
                    templowyear = data['almanac']['temp_low']['recordyear']
                # now output
                irc.reply("{0} :: {1} {2} {3} {4} {5} {6}".format(self._bold('Almanac:'),\
                    temphighnormal,temphighrecord,temphighyear,\
                        templownormal, templowrecord, templowyear))

           
    wunderground = wrap(wunderground, [getopts({'alerts':'',
                                                'almanac':'',
                                                'astronomy':'',
                                                'days':('int'),
                                                'pressure':'',
                                                'wind':'',
                                                'uv':'',
                                                'visibility':'',
                                                'dewpoint':'',
                                                'metric':''}), optional('text')])

dbfilename = conf.supybot.directories.data.dirize("Weather.db")

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
