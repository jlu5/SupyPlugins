###
# Copyright (c) 2012-2014, spline
# All rights reserved.
###

import supybot.conf as conf
import supybot.registry as registry
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('Weather')

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Weather', True)

Weather = conf.registerPlugin('Weather')
conf.registerGlobalValue(Weather, 'apiKey',
    registry.String('', ("""Sets the API key for the plugin. You can obtain an API key at http://www.wunderground.com/weather/api/."""), private=True))
conf.registerChannelValue(Weather, 'useImperial',
    registry.Boolean(True, ("""Determines whether imperial units (Fahrenheit, etc.) will be used.""")))
conf.registerGlobalValue(Weather,'forecast',
    registry.Boolean(True, ("""Determines whether forecasts will be displayed by default.""")))
conf.registerGlobalValue(Weather,'alerts',
    registry.Boolean(False, ("""Determines whether forecasts will be displayed by default.""")))
conf.registerGlobalValue(Weather, 'almanac',
    registry.Boolean(False, ("""Determines whether almanac will be displayed by default.""")))
conf.registerGlobalValue(Weather, 'astronomy',
    registry.Boolean(False, ("""Determines whether astronomy will be displayed by default.""")))
conf.registerGlobalValue(Weather, 'showPressure',
    registry.Boolean(False, ("""Determines whether pressure will be displayed by default.""")))
conf.registerGlobalValue(Weather, 'showWind',
    registry.Boolean(False, ("""Determines whether winde will be displayed by default.""")))
conf.registerGlobalValue(Weather, 'showUpdated',
    registry.Boolean(False, ("""Determines whether the bot will show the data's "last updated" time by default.""")))
conf.registerGlobalValue(Weather, 'lang',
    registry.String('EN', ("""Determines the language used by the plugin.""")))
conf.registerChannelValue(Weather, 'disableColoredTemp',
    registry.Boolean(False, """If True, this will disable coloring temperatures based on values."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=250:
