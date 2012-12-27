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
            id = ['x', nick.lower()][0]
        except:
            id = '10121'
        self['x', nick.lower()] = (id, metric,) 

class Weather(callbacks.Plugin):
    """Add the help for "@plugin help Weather" here
    This should describe *how* to use this plugin."""
    threaded = True

    #######################
    # WeatherDB functions #
    #######################
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
    
    # FORMATTING
    def _bold(self, string):
        return ircutils.bold(string)

    def _blue(self, string):
        return ircutils.mircColor(string, 'blue')

    def _bu(self, string):
        return ircutils.underline(ircutils.bold(string))

    def _red(self, string):
        return ircutils.mircColor(string, 'red')
    
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
        Fetch weather for location.
        It is best to specify a zipcode or specific location with country. Ex: 10152 or Sydney, Australia
        
        """
        
        # first, check if we have an API key. Useless w/o this.
        if not self.keycheck(irc):
            return False
        
        # now check if we have a location. if no location, use the userdb. 
        if not optinput:
            try:
                optinput = self.db.getId(msg.nick)
            except KeyError:
                irc.reply("I did not find a preset location for you. Set via: setweather location or specify a location")
                return
        
        # store all of our formatting variables
        args = {'imperial':self.registryValue('useImperial', msg.args[0]) }
        
        # handle optlist (getopts)
        if optlist:
            for (key, value) in optlist:
                if key == "metric":
                    args['imperial'] = False
                    
        url = 'http://api.wunderground.com/api/%s/conditions/lang:EN/bestfct:1/pws:0/q/%s.json' % (self.APIKEY, optinput)
        self.log.info(url)
                    
        # try and query.                        
        try: 
            request = urllib2.Request(url)
            u = urllib2.urlopen(request)
        except:
            irc.reply("Failed to load url: %s" % url)
            return
        
        # process the json.
        data = json.load(u)
        
        # check if we got errors and return.
        if 'error' in data['response']:
            errortype = data['response']['error']['type']
            errordesc = data['response']['error']['description']
            irc.reply("{0} I got an error searching for {1}. ({2}: {3})".format(self._red("ERROR:"), optinput, errortype, errordesc))
            return

        # if there is more than one city matching.
        if 'results' in data['response']:
            output = [item['city'] + ", " + item['state'] + " (" + item['country_name'] + ")" for item in data['response']['results']]
            irc.reply("More than 1 city matched your query, try being more specific: {0}".format(" | ".join(output)))
            return
        
        # last sanity check
        if not data['current_observation']:
            irc.reply("{0} something went horribly wrong looking up weather for {1}. Contact the plugin owner.".format(self._red("ERROR:"), optinput))
            return

        # basics for weather output.        
        data = data['current_observation']
        weather = data['weather']
        location = data['display_location']['full']
        observation = data['observation_time_rfc822']
        humidity = data['relative_humidity']
        wind = data['wind_string']
        uv = data['UV']
        
        # all conditionals for imperial/metric
        if args['imperial']:
            temp = data['temp_f']
            pressure = data['pressure_mb']
            dewpoint = data['dewpoint_f']
            heatindex = data['heat_index_f']
            windchill = data['windchill_f']
            feelslike = data['feelslike_f']
            visibility = data['visibility_mi']
        else:
            temp = data['temp_c']
            pressure = data['pressure_in']
            dewpoint = data['dewpoint_c']
            heatindex = data['heat_index_c']
            windchill = data['windchill_c']
            feelslike = data['feelslike_c']
            visibility = data['visibility_km']

        irc.reply(temp)

    wunderground = wrap(wunderground, [getopts({'metric':''}), optional('text')])

dbfilename = conf.supybot.directories.data.dirize("Weather.db")

Class = Weather

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=250:
