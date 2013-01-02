Supybot-Weather
===============

Overview
    
    This is a Supybot plugin for displaying Weather via Weather Underground (http://www.wunderground.com)
    They've got a nice JSON api that is free to use when you register and grab an API key. You will need
    an API key to use this plugin. Configure it via:
    
        /msg bot config plugin.Weather.apiKey <apiKey>
    
    I made this plugin because quite a few Weather plugins didn't work well and WunderWeather, which uses
    this API, is on their older XML api that they don't have documented anymore and, one would assume, will
    be depreciated at some point. 
    
    There are a ton of options to configure. You can look through these via /msg <bot> config search Weather
    Many of these are also available via --options when calling the wunderground command.
    
    I suggest adding an alias to this command to make it easier.
    
        /msg bot Alias add weather wunderground
    
    Another feature that will make you and your users happy is an internal database that can remember your 
    location and setting for metric. I've seen this before with another bot and wanted to implement this.
    Basically, instead of having to type wunderground 10152 (or wherever you are), you can just type in
    wunderground. This can be done via setting a location with the setweather command.
    
        /msg <bot> setweather 10152
        /msg <bot> setmetric False (to use imperial units)
        
    The bot's db is very simple and only remembers a nick and setting. So, if you change nicks, it will not
    remember you unless you set it on this new nick. 
    
    Use:
        /msg <bot> getweather
        /msg <bot> getmetric 
        
    To check settings here. This is optional but a neat feature. This only works if you don't give it an input.
    So, if you /msg bot wunderground --metric, it will display the weather you set in setweather but in --metric.

Options

    This plugin has a bit of configuration that can be done with it. We'll start with the basics:
    
    - useImperial:
    We display using non-metric units. For the rest of the world who uses them, you may set this
    per channel or in the config via the:
    
        plugins.Weather.useImperial configuration variable (True/False)
        
    You may also use --metric when calling to get metric units.
    
    - languages:
    By default, it is set to English. Weather Underground has a variety of language support
    documented here: http://api.wunderground.com/weather/api/d/docs?d=language-support
    If you do not want to use English, you can set this via one of the codes above:
    
        config plugins.Weather.lang EN (replace EN with the 2 letter language code)
    
    - disableANSI:
    By default, ANSI is on. Color/bold on output makes things a bit easier to read.
    If you do not want any color or bold in the output for a specific channel, you can:
        
        /msg bot channel #channelname plugins.Weather.disableANSI True
        
        or
        
        /msg bot config plugins.Weather.disableANSI True
    
    - forecastDays:
    By default, the plugin is set to display 4 days of forecast with --forecast
    I do not have the code to show more since forecasts beyond this are unreliable.
    If you want less, you can configure this between 1 and 4.
    
        /msg bot config plugins.Weather.forecastDays 4
    
Documentation

    Some links:
        - Main documentation: http://www.wunderground.com/weather/api/
        # https://github.com/davidwilemski/Weather/blob/master/weather.py
        # https://bitbucket.org/rizon/pypsd/src/8f975a375ab4/modules/internets/api/weather.py
        # http://ronie.googlecode.com/svn-history/r283/trunk/weather.wunderground/default.py
        # http://www.wunderground.com/weather/api/
    
