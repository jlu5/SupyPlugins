###
# Copyright (c) 2021, James Lu
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
import urllib.parse

# local modules
from . import parsebird, parsetrace

# 3rd party
import requests

from supybot import utils, plugins, callbacks
from supybot.commands import wrap
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('BirdLGGo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class BirdLGGo(callbacks.Plugin):
    """API client (show route / traceroute) for Bird-lg-go"""
    threaded = True

    def lg_post_request(self, irc, msg, query):
        url = urllib.parse.urljoin(self.registryValue("lgServer", network=irc.network, channel=msg.channel), "/api/")
        if not url:
            raise irc.error("No looking glass server specified - please set plugins.birdlggo.lgserver", Raise=True)
        elif not query.get("servers"):
            raise irc.error("No target nodes specified - please set plugins.birdlggo.nodes", Raise=True)

        req = requests.post(url, json=query)

        resp = req.json()
        if resp.get("error"):
            raise irc.error("Error from looking glass: " + resp["error"], Raise=True)
        else:
            return resp["result"]

    @wrap(['something'])
    def traceroute(self, irc, msg, args, target):
        """<target>

        Sends a traceroute to the target host or IP.
        """
        nodes = self.registryValue("nodes", network=irc.network, channel=msg.channel)
        query = {
            "servers": nodes,
            "type": "traceroute",
            "args": target
        }
        results = self.lg_post_request(irc, msg, query)

        for result in results:
            parsed_result = parsetrace.parse_traceroute(result["data"])
            server = result["server"]

            ips = " ".join(parsed_result.ips)
            latency = parsed_result.latency or "(timed out)"
            notes = ""
            if parsed_result.notes:
                notes = "- " + ", ".join(parsed_result.notes)

            irc.reply(f"{server} -> {target}: {latency} | {ips} {notes}")

    @wrap(['something'])
    def showroute(self, irc, msg, args, target):
        """<target>

        Shows the preferred BIRD route for the given target.
        """
        nodes = self.registryValue("nodes", network=irc.network, channel=msg.channel)
        query = {
            "servers": nodes,
            "type": "bird",
            "args": f"show route for {target} all primary"
        }
        results = self.lg_post_request(irc, msg, query)

        for result in results:
            parsed_result = parsebird.parse_bird(result["data"])
            server = result["server"]

            s = f"{server} -> {target}: {parsed_result.route_type} {parsed_result.via} [Type: {parsed_result.route_origin}] [Pref: {parsed_result.route_preference}]"
            if parsed_result.bgp_as_path:
                path = " ".join(parsed_result.bgp_as_path)
                s += f" [AS path: {path}]"

            irc.reply(s)

Class = BirdLGGo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=120:
