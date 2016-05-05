# coding: utf-8
###
# Copyright (c) 2014-2015, James Lu
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
from __future__ import unicode_literals

import re
try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Beautiful Soup 4 is required for this plugin: "
                      "http://www.crummy.com/software/BeautifulSoup/bs4/"
                      "doc/#installing-beautiful-soup")
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PortLookup')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class PortLookup(callbacks.Plugin):
    """Looks up commonly used TCP and UDP port numbers."""
    @wrap(['positiveInt'])
    def port(self, irc, msg, args, port):
        """<port number>

        Looks up <port number> in Wikipedia's list of ports at
        https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers.
        """
        if port > 65535:
            irc.error('Port numbers cannot be greater than 65535.', Raise=True)
        if BeautifulSoup is None:
            irc.error("Beautiful Soup 4 is required for this plugin: get it"
                      " at http://www.crummy.com/software/BeautifulSoup/bs4/"
                      "doc/#installing-beautiful-soup", Raise=True)
        url = "https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers"
        fd = utils.web.getUrlFd(url)
        soup = BeautifulSoup(fd)
        if port >= 49152:
            results = ['The range 49152–65535 (2^15+2^14 to 2^16−1)—above the '
                       'registered ports—contains dynamic or private ports that '
                       'cannot be registered with IANA. This range is used for '
                       'custom or temporary purposes and for automatic '
                       'allocation of ephemeral ports.']
        else:
            results = []
            for tr in soup.find_all('tr'):
                tds = tr.find_all('td')
                if not tds:
                    continue
                portnum = tds[0].text
                if '–' in portnum:
                    startport, endport = map(int, portnum.split('–'))
                    p = range(startport, endport+1)
                else:
                    try:
                        p = [int(portnum)]
                    except ValueError:
                        continue
                if port in p:
                    text = tds[3].text
                    # Remove inline citations (text[1][2][3]), citation needed tags, etc.
                    text = re.sub('\[.*?]', '', text)

                    # List the port notes (tags such as "Official", "TCP", "UDP", etc.)
                    # This is every <td> tag except the 4th one, which is the description parsed
                    # above.
                    notes = [t.text.strip() for t in tds[:3]+tds[4:]]
                    notes = '; '.join(filter(None, notes))

                    # Remove \n, etc. in fields to prevent output corruption.
                    s = utils.str.normalizeWhitespace('%s [%s]' % (ircutils.bold(text), notes))
                    results.append(s)
        if results:
            irc.reply(format('%s: %L', ircutils.bold(ircutils.underline(port)), results))
        else:
            irc.error(_('No results found.'))
Class = PortLookup

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
