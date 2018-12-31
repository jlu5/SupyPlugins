###
# Copyright (c) 2018, James Lu <james@overdrivenetworks.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###
import json

from supybot import utils, plugins, ircutils, callbacks, world, conf
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NuWeather')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from .config import BACKENDS
from .local import accountsdb

HEADERS = {
    'User-agent': 'Mozilla/5.0 (compatible; Supybot/Limnoria %s; NuWeather weather plugin)' % conf.version
}

class NuWeather(callbacks.Plugin):
    """Weather plugin for Limnoria"""
    threaded = True

    def __init__(self, irc):
        super().__init__(irc)
        self.db = accountsdb.AccountsDB("NuWeather", 'NuWeather.db')
        world.flushers.append(self.db.flush)

    def die(self):
        world.flushers.remove(self.db.flush)
        self.db.flush()
        super().die()

    def _format_temp(self, f, c=None, msg=None):
        f = float(f)
        if f < 10:
            color = 'light blue'
        elif f < 32:
            color = 'teal'
        elif f < 50:
            color = 'blue'
        elif f < 60:
            color = 'light green'
        elif f < 70:
            color = 'green'
        elif f < 80:
            color = 'yellow'
        elif f < 90:
            color = 'orange'
        else:
            color = 'red'
        # Round to nearest tenth for display purposes
        if c is None:
            c = round((f - 32) * 5/9, 1)
        else:
            c = round(c, 1)
        f = round(f, 1)

        displaymode = self.registryValue('units.temperature', msg.args[0] if msg else None)
        if displaymode == 'F/C':
            string = '%sF/%sC' % (f, c)
        elif displaymode == 'C/F':
            string = '%sC/%sF' % (c, f)
        elif displaymode == 'F':
            string = '%sF' % f
        elif displaymode == 'C':
            string = '%sC' % c
        else:
            raise ValueError("Unknown display mode for temperature.")
        return ircutils.mircColor(string, color)

    @staticmethod
    def _format_uv(uv):
        # From https://en.wikipedia.org/wiki/Ultraviolet_index#Index_usage 2018-12-30
        uv = float(uv)
        if uv <= 2.9:
            color, risk = 'green', 'Low'
        elif uv <= 5.9:
            color, risk = 'yellow', 'Moderate'
        elif uv <= 7.9:
            color, risk = 'orange', 'High'
        elif uv <= 10.9:
            color, risk = 'red', 'Very high'
        else:
            # Closest we have to violet
            color, risk = 'pink', 'Extreme'
        string = '%d (%s)' % (uv, risk)
        return ircutils.mircColor(string, color)

    def _apixu_fetcher(self, location):
        """Grabs weather data from Apixu."""
        apikey = self.registryValue('apikeys.apixu')
        if not apikey:
            raise callbacks.Error(_("Please configure the apixu API key in plugins.nuweather.apikeys.apixu."))
        url = 'https://api.apixu.com/v1/forecast.json?' + utils.web.urlencode({
            'key': apikey,
            'q': location,
        })
        self.log.debug('NuWeather: using url %s', url)

        f = utils.web.getUrl(url, headers=HEADERS).decode('utf-8')
        data = json.loads(f)

        location = data['location']
        if location['region']:
            location = "%s, %s, %s" % (location['name'], location['region'], location['country'])
        else:
            location = "%s, %s" % (location['name'], location['country'])

        # current conditions
        currentdata = data['current']
        condition = currentdata['condition']['text']
        cur_temp = self._format_temp(currentdata['temp_f'], currentdata['temp_c'])
        feels_like = self._format_temp(currentdata['feelslike_f'], currentdata['feelslike_c'])
        humidity = currentdata['humidity']
        precip = '%smm/%sin' % (currentdata['precip_mm'], currentdata['precip_in'])
        wind = '%smph/%skph %s' % (currentdata['wind_mph'], currentdata['wind_kph'], currentdata['wind_dir'])
        visibility = '%skm/%smi' % (currentdata['vis_km'], currentdata['vis_miles'])
        uv = self._format_uv(currentdata['uv'])

        current = _('%s %s (Humidity: %s%%) | \x02Feels like:\x02 %s | \x02Precip:\x02 %s '
                    '| \x02Wind:\x02 %s | \x02Visibility:\x02 %s | \x02UV:\x02 %s') % (
            condition, cur_temp, humidity, feels_like, precip, wind, visibility, uv
        )

        # daily forecast
        forecastdata = data['forecast']['forecastday'][0]
        condition = forecastdata['day']['condition']['text']
        maxtemp = self._format_temp(forecastdata['day']['maxtemp_f'], forecastdata['day']['maxtemp_c'])
        mintemp = self._format_temp(forecastdata['day']['mintemp_f'], forecastdata['day']['mintemp_c'])
        forecast = _('%s, Low: %s High: %s' % (condition, mintemp, maxtemp))

        s = _('%s :: %s | \x02Today:\x02 %s | Powered by \x02Apixu\x02') % (
            ircutils.bold(location), current, forecast
        )
        return s

    @wrap([getopts({'user': 'nick', 'backend': None}), additional('text')])
    def weather(self, irc, msg, args, optlist, location):
        """
        [--user <othernick>] [--backend <backend>] [<location>]

        Fetches weather and forecast information for <location>. <location> can be left blank if you have a previously set location (via 'setweather').

        If the --user option is specified, show weather for the saved location of that nick, instead of the caller.
        """
        optlist = dict(optlist)
        # Default to the caller
        if optlist.get('user'):
            try:
                hostmask = irc.state.nickToHostmask(optlist['user'])
            except KeyError:
                irc.error(_("I don't know who %r is.") % optlist['user'], Raise=True)
        else:
            hostmask = msg.prefix
        # Can be specified location or default one in DB
        location = location or self.db.get(hostmask)

        if not location:
            irc.error(_("I did not find a preset location for your nick. Please set one via 'setweather <location>'."), Raise=True)

        backend = optlist.get('backend', self.registryValue('defaultBackend', msg.args[0]))
        if backend not in BACKENDS:
            irc.error(_("Unknown weather backend %s. Valid ones are: %s") % (backend, ', '.join(BACKENDS)), Raise=True)

        backend_func = getattr(self, '_%s_fetcher' % backend)
        s = backend_func(location)
        irc.reply(s)

    @wrap(['text'])
    def setweather(self, irc, msg, args, location):
        """<location>

        Saves the weather location for your bot account, or hostmask if you are not registered.
        """
        self.db.set(msg.prefix, location)
        irc.replySuccess()

Class = NuWeather


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
