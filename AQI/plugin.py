###
# Copyright (c) 2019, James Lu <james@overdrivenetworks.com>
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

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('AQI')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class AQI(callbacks.Plugin):
    """Retrieves air quality index info from aqicn.org"""
    threaded = True

    @staticmethod
    def _format_aqi(aqino):
        """Formats the given AQINO index."""
        # Retrieved from http://aqicn.org/scale/ 20190603
        f = lambda *args, **kwargs: ircutils.bold(ircutils.mircColor(*args, **kwargs))

        if not isinstance(aqino, int):
            return f(_(' %s No data ') % aqino,
                     fg='white', bg='black')

        if aqino <= 50:
            return f(_(' %s (Good) ') % aqino,
                     fg='white', bg='green')
        elif aqino <= 100:
            return f(_(' %s (Moderate) ') % aqino,
                     fg='black', bg='yellow')
        elif aqino <= 150:
            return f(_(' %s (Unhealthy for Sensitive Groups) ') % aqino,
                     fg='black', bg='orange')
        elif aqino <= 200:
            return f(_(' %s (Unhealthy) ') % aqino,
                     fg='white', bg='red')
        elif aqino <= 300:
            return f(_(' %s (Very Unhealthy) ') % aqino,
                     fg='white', bg='purple')
        else:
            return f(_(' %s (Hazardous) ') % aqino,
                     fg='white', bg='brown')

    @wrap([getopts({'geocode-backend': None}), "text"])
    def aqi(self, irc, msg, args, optlist, location):
        """[--geocode-backend <backend>] <location>

        Looks up Air Quality Index information for <location> using aqicn.org.

        --geocode-backend can be set to "native" or any geocoding backend supported by the NuWeather plugin. If nothing is given, this defaults to the backend set in 'plugins.aqicn.geocodeBackend'

        If the geocoding backend is empty, aqicn's built-in city search will be used: this supports only basic city names as well as aqicn station IDs in the form "@1234".
        """
        apikey = self.registryValue("apiKey")
        if not apikey:
            irc.error("The API Key is not set. Please set it via the 'plugins.aqicn.apikey' config "
                      "variable. You can sign up for an API key at https://aqicn.org/api", Raise=True)

        # We can use aqicn.org's builtin search or one of NuWeather's geocoding backends
        geocode_backend = dict(optlist).get('geocode-backend', self.registryValue('geocodeBackend', msg.args[0]))

        if geocode_backend not in {'', 'native'}:
            nuweather = irc.getCallback('NuWeather')
            if not nuweather:
                irc.error("The NuWeather plugin is required for more advanced geolookup.", Raise=True)
            result = nuweather._geocode(location, geobackend=geocode_backend)

            # Set location to geo:lat:lon, per https://aqicn.org/json-api/doc/#api-Geolocalized_Feed-GetGeolocFeed
            location = 'geo:%s;%s' % (result[0], result[1])

        url = 'https://api.waqi.info/feed/%s/?%s' % (utils.web.urlquote(location), utils.web.urlencode({'token': apikey}))
        self.log.debug('AQI: using URL %s', url)

        f = utils.web.getUrl(url)
        data = json.loads(f.decode('utf-8'))

        if data['status'] == 'error':
            irc.error('Got API error: %s' % data['data'], Raise=True)
        else:
            # AQI value: usually a number, except for when there's no data (a literal '-')
            aqino = data['data']['aqi']

            placename = data['data']['city']['name']
            infourl = data['data']['city']['url']
            attribs = [obj['name'] for obj in data['data']['attributions']]

            formatted_aqi = self._format_aqi(aqino)
            s = format(_('%s :: %s %u; from %L'), ircutils.bold(placename), formatted_aqi, infourl, attribs)
            irc.reply(s)

Class = AQI


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
