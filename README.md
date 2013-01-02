Supybot-Weather
===============

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
    
        /msg bot config plugins.Weather.lang EN (replace EN with the 2 letter language code)
    
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
    
       
    
Supybot plugin for displaying weather and forecast data from Weather Underground (wunderground.com) API
    # language support http://www.wunderground.com/weather/api/d/docs?d=language-support
    # https://github.com/davidwilemski/Weather/blob/master/weather.py
    # https://bitbucket.org/rizon/pypsd/src/8f975a375ab4/modules/internets/api/weather.py
    # http://ronie.googlecode.com/svn-history/r283/trunk/weather.wunderground/default.py
    # http://api.wunderground.com/api/fc7cb609a45365fa/conditions/lang:EN/bestfct:1/pws:0/q/03062.json
    # http://www.wunderground.com/weather/api/
    
