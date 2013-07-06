Supybot-Weather
===============

Update

    20130705 - I have updated the user settings system as I've got a ton of requests to go to individual
    settings.

    setmetric and setcolortemp have been folded into the setuser command.

    Please see the setuser help for all settings, outside of setweather, for a user.

Overview

    This is a Supybot plugin for displaying Weather via Weather Underground (http://www.wunderground.com)
    They've got a nice JSON api that is free to use when you register and grab an API key.

    I made this plugin because quite a few Weather plugins didn't work well and WunderWeather, which uses
    this API, is on their older XML api that they don't have documented anymore and, one would assume, will
    be depreciated at some point.

    Besides a few of the ideas like having a user database, colorized temp, most of the code is mine.

Instructions

    NOTICE: If you were using the older version of this plugin before June 2013,
    you _MUST_ delete the older Weather.db file in the Supybot data directory.
    Normally, this is at <supybotdir>/data/Weather.db
    The internal DB is not compatable and must be deleted before.

    First, you will need to register for a free API key. Signup takes less than a minute at:

        http://www.wunderground.com/weather/api/

    You will need an API key to use this plugin. Configure it via:

        /msg <bot> config plugin.Weather.apiKey <apiKey>

    Now reload the plugin:

        /msg <bot> reload Weather

    You can now use the basic functionality by:

        /msg <bot> wunderground 10012 (or your zipcode)

    I suggest adding an alias to this command to make it easier.

        /msg <bot> Alias add weather wunderground
        /msg <bot> Alias add w wunderground

Options

    There are a ton of options to configure. You can look through these via /msg <bot> config search Weather
    Many of these are also available via --help when calling the wunderground command.


    Another feature that will make you and your users happy is an internal database that can remember your
    location, setting for metric, and color temperature.
    
    Basically, instead of having to type wunderground 10152 (or wherever you are), you can just type in
    wunderground. This can be done via setting a location with the setweather command.

        /msg <bot> setweather 10152
        /msg <bot> setuser metric False (to use imperial units)
        /msg <bot> setuser colortemp False (or true)

    The bot's db is very simple and only remembers a nick and setting. So, if you change nicks, it will not
    remember you unless you set it on this new nick.

Options

    This plugin has a bit of configuration that can be done with it. We'll start with the basics:

    - useImperial:
    We display using non-metric units. For the rest of the world who uses them, you may set this
    per channel or in the config via the:

        /msg <bot> config plugins.Weather.useImperial configuration variable (True/False)

    You may also use --metric when calling to get metric units.

    - languages:
    By default, it is set to English. Weather Underground has a variety of language support
    documented here: http://api.wunderground.com/weather/api/d/docs?d=language-support
    If you do not want to use English, you can set this via one of the codes above:

        /msg <bot> config plugins.Weather.lang EN (replace EN with the 2 letter language code)


    - disableColorTemp
    On a similar note, I coded a neat "color" to temperature function that will color any temperature
    on a basis of what it is (works for metric, too). Think of how temperature maps are done where
    you would see red/orange/yellow if it's "hot", green if "moderate", and blue if its "cold".
    By default, I have this ON. This can also be personalized via /msg <bot> setcolortemp True/False
    once a user is in the database. You can turn it off like this:

        /msg <bot> config plugins.Weather.disableColorTemp True

Documentation

    Some links:
        # Main documentation: http://www.wunderground.com/weather/api/
        # https://github.com/davidwilemski/Weather/blob/master/weather.py
        # https://bitbucket.org/rizon/pypsd/src/8f975a375ab4/modules/internets/api/weather.py
        # http://ronie.googlecode.com/svn-history/r283/trunk/weather.wunderground/default.py
