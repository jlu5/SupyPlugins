###
# Copyright (c) 2014-2018, James Lu <james@overdrivenetworks.com>
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
import collections

from supybot import utils, plugins, ircutils, callbacks, log
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('FML')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

from bs4 import BeautifulSoup

class FML(callbacks.Plugin):
    """Displays entries from fmylife.com."""
    threaded = True

    URL_RANDOM = 'https://www.fmylife.com/random'
    URL_ARTICLE = 'https://www.fmylife.com/article/-_%s.html'  # subst in the ID
    cached_results = collections.deque()

    @staticmethod
    def _parse_panel(panel, fml_id=None):
        """Parses a FML entry panel for data. Returns a (fml_id, text, num_upvotes, num_downvotes) tuple."""
        if panel:
            content = panel.find(class_='article-link')
            log.debug("FML: parsing panel %s", panel)
            log.debug("FML: parsing content %s", content)

            if not content:
                return
            text = content.text.strip()
            if not text.endswith(' FML'):  # Ignore ads, promos, previews
                return

            # If not given, extract the FML ID from the link
            if fml_id is None and content.name == 'a':
                link = content['href']
                fml_id = link.rsplit('_', 1)[-1].split('.', 1)[0]

            vote_counts = panel.find_all('div', class_='vote-count')
            upvotes = vote_counts[0].text.strip()
            downvotes = vote_counts[1].text.strip()

            data = (fml_id, text, upvotes, downvotes)
            return data

    def _get_random_entries(self):
        """Fetches and caches random FML entries. Returns the amount of entries retrieved."""
        html = utils.web.getUrl(self.URL_RANDOM)
        soup = BeautifulSoup(html)

        results_count = 0
        for panel in soup.find_all('div', class_='article-contents'):
            data = self._parse_panel(panel)
            if data:
                self.log.debug('FML: got entry: %s', str(data))
                self.cached_results.append(data)
                results_count += 1

        self.log.debug('FML: got total of %s results, cache size: %s', results_count,
                       len(self.cached_results))
        return results_count

    def fml(self, irc, msg, args, query):
        """[<id>]

        Displays an entry from fmylife.com. If <id> is not given, fetch a random entry from the API."""
        if query:  # Explicit ID given
            html = utils.web.getUrl(self.URL_ARTICLE % query)
            soup = BeautifulSoup(html)
            panel = soup.find('div', class_='article-contents')
            data = self._parse_panel(panel, fml_id=query)
        else:  # Random search
            if not len(self.cached_results):
                if not self._get_random_entries():
                    irc.error("Could not fetch new FML entries - try again later.", Raise=True)
            data = self.cached_results.popleft()

        if not data:
            irc.error(_("Entry not found or error processing data."), Raise=True)
        fml_id, text, num_upvotes, num_downvotes = data

        votes = ircutils.bold("[Agreed: %s / Deserved: %s]" % (num_upvotes, num_downvotes))
        if self.registryValue("showInfo", msg.args[0]):
            url = self.URL_ARTICLE % fml_id
            s = format('\x02#%i\x02: %s - %s %u', fml_id, text, votes, url)
        else:
            s = format('%s - %s', text, votes)

        irc.reply(s)

    fml = wrap(fml, [additional('positiveInt')])

Class = FML


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
