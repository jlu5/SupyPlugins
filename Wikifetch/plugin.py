###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
# Copyright (c) 2015-2023 James Lu
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
import re
import urllib.parse

from supybot import callbacks, conf, ircutils, plugins, utils
from supybot.commands import wrap, getopts, additional
try:
    from supybot.i18n import PluginInternationalization, internationalizeDocstring
    _ = PluginInternationalization('Wikifetch')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

from bs4 import BeautifulSoup
import mwparserfromhell

HEADERS = {
    'User-agent': 'Mozilla/5.0 (compatible; Supybot/Limnoria %s; Wikifetch plugin)' % conf.version
}

class Wikifetch(callbacks.Plugin):
    """Grabs data from Wikipedia and other MediaWiki-powered sites."""
    threaded = True

    def _mw_api_call(self, baseurl, params):
        """Performs a GET call to the MediaWiki API."""
        url = f"{baseurl}?{params}"

        self.log.debug('Wikifetch: fetching link %s', url)
        with utils.web.getUrlFd(url, headers=HEADERS) as fd:
            api_data = json.load(fd)

        if isinstance(api_data, dict):
            if error := api_data.get('error'):
                error_code = error['code']
                error_info = error['info']
                raise callbacks.Error(f"MediaWiki API Error: {error_code} - {error_info} - {url}")

        return api_data

    def _mw_fetch_article(self, baseurl, title):
        """Return the first paragraph and canonical URL of a wiki page."""
        params = urllib.parse.urlencode({
            'action': 'parse',
            'page': title,
            'prop': 'wikitext|headhtml',
            'formatversion': 2,
            'format': 'json',
            'redirects': True
        })
        api_data = self._mw_api_call(baseurl, params)

        page_title = api_data['parse']['title']
        content = api_data['parse']['wikitext']
        html_head = api_data['parse']['headhtml']
        mw = mwparserfromhell.parse(content)
        for line in mw.strip_code().splitlines():
            # Ignore stray image references that strip_code leaves behind
            if re.search(r'\|?thumb\|', line):
                continue
            elif len(line) < 10:
                continue
            text = utils.str.normalizeWhitespace(line)
            break
        else:
            raise callbacks.Error(f"No text paragraph found for page {page_title!r}")

        soup = BeautifulSoup(html_head, features="lxml")
        url = ''
        if canonical_link := soup.find('link', rel='canonical'):
            # Wikipedia
            url = canonical_link.attrs['href']
        elif og_url := soup.find('meta', property='og:url'):
            # Fandom
            url = og_url.attrs['content']

        return (text, url)

    def _mw_search(self, baseurl, searchquery):
        """Return results from a MediaWiki search."""
        params = urllib.parse.urlencode({
            'action': 'opensearch',
            'search': searchquery,
            'format': 'json',
        })
        api_data = self._mw_api_call(baseurl, params)

        search_result_titles = api_data[1]
        if not search_result_titles:
            raise callbacks.Error(f"No search results for {searchquery!r}")
        return search_result_titles

    def _wiki(self, irc, baseurl, query):
        search_results = self._mw_search(baseurl, query)
        page_title = search_results[0]
        text, url = self._mw_fetch_article(baseurl, page_title)
        if url:
            irc.reply(utils.str.format("%s - %u", text, url))
        else:
            irc.reply(text)

    @internationalizeDocstring
    @wrap([getopts({'lang': 'somethingWithoutSpaces'}), 'text'])
    def wiki(self, irc, msg, args, optlist, searchquery):
        """<search query>

        Returns the first paragraph of a Wikipedia article.
        """
        optlist = dict(optlist)
        lang = optlist.get('lang') or \
            self.registryValue('wikipedia.lang', channel=msg.channel, network=irc.network)

        baseurl = f'https://{lang}.wikipedia.org/w/api.php'
        self._wiki(irc, baseurl, searchquery)

    @wrap(['somethingWithoutSpaces', 'text'])
    def fandom(self, irc, msg, args, wiki_subdomain, searchquery):
        """<wiki subdomain> <title>

        Returns the first paragraph of a Fandom article.
        """
        baseurl = f'https://{wiki_subdomain}.fandom.com/api.php'
        self._wiki(irc, baseurl, searchquery)

    @wrap(['somethingWithoutSpaces', 'text'])
    def wikigg(self, irc, msg, args, wiki_subdomain, searchquery):
        """<wiki subdomain> <title>

        Returns the first paragraph of a wiki.gg article.
        """
        baseurl = f'https://{wiki_subdomain}.wiki.gg/api.php'
        self._wiki(irc, baseurl, searchquery)

Class = Wikifetch
