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
from xml.etree import ElementTree
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('FML')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class FML(callbacks.Plugin):
    """Displays entries from fmylife.com."""
    threaded = True

    def fml(self, irc, msg, args, query):
        """[<id>]

        Displays an entry from fmylife.com. If <id>
        is not given, fetch a random entry from the API."""
        query = query or 'random'
        url = ('http://api.betacie.com/view/%s/nocomment'
              '?key=4be9c43fc03fe&language=en' % query)
        try:
            data = utils.web.getUrl(url)
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)
        tree = ElementTree.fromstring(data.decode('utf-8'))
        tree = tree.find('items/item')

        try:
            category = tree.find('category').text
            text = tree.find('text').text
            fmlid = tree.attrib['id']
            url = tree.find('short_url').text
        except AttributeError as e:
            self.log.debug("FML: Error fetching FML %s from URL %s: %s",
                           query, url, e)
            irc.error("That FML does not exist or there was an error "
                      "fetching data from the API.", Raise=True)

        if not fmlid:
            irc.error("That FML does not exist.", Raise=True)

        votes = ircutils.bold("[Agreed: %s / Deserved: %s]" %
                              (tree.find('agree').text,
                              tree.find('deserved').text))
        s = format('\x02#%i [%s]\x02: %s - %s %u', fmlid,
                   category, text, votes, url)
        irc.reply(s)
    fml = wrap(fml, [additional('positiveInt')])

Class = FML


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
