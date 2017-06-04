###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
# Copyright (c) 2015,2017 James Lu <james@overdrivenetworks.com>
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

import re
import sys
import lxml.html
import supybot.utils as utils
from supybot.commands import wrap, getopts, additional
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('Wikifetch')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

if sys.version_info[0] >= 3:
    from urllib.parse import quote_plus
else:
    from urllib import quote_plus

class Wikifetch(callbacks.Plugin):
    """Grabs data from Wikipedia and other MediaWiki-powered sites."""
    threaded = True

    # This defines a series of suffixes this should be added after the domain name.
    SPECIAL_URLS = {'wikia.com': '/wiki',
                    'wikipedia.org': '/wiki',
                    'wiki.archlinux.org': '/index.php',
                    'wiki.gentoo.org': '/wiki',
                    'mediawiki.org': '/wiki',
                    'wikimedia.org': '/wiki',
                   }

    def _get_article_tree(self, baseurl, query, use_mw_parsing=True):
        """
        Returns a wiki article tree given the base URL and search query. baseurl can be None,
        in which case, searching is skipped and the search query will be treated as a raw address.
        """

        if baseurl is None:
            addr = query
        else:
            # Different instances of MediaWiki use different URLs... This tries
            # to make the parser work for most sites, but still use resonable defaults
            # such as filling in http:// and appending /wiki to links...
            baseurl = baseurl.lower()
            for match, suffix in self.SPECIAL_URLS.items():
                if match in baseurl:
                    baseurl += suffix
                    break

            # Add http:// to the URL if a scheme isn't specified
            if not baseurl.startswith(('http://', 'https://')):
                baseurl = 'http://' + baseurl

            if use_mw_parsing:
                # first, we get the page
                addr = '%s/Special:Search?search=%s' % \
                            (baseurl, quote_plus(query))
            else:
                addr = '%s/%s' % (baseurl, query)

        self.log.debug('Wikifetch: using URL %s', addr)

        try:
            article = utils.web.getUrl(addr, timeout=3)
        except utils.web.Error:
            self.log.exception('Failed to fetch link %s', addr)
            raise

        if sys.version_info[0] >= 3:
            article = article.decode()

        tree = lxml.html.document_fromstring(article)
        return (tree, article, addr)

    def _wiki(self, irc, msg, search, baseurl, use_mw_parsing=True):
        """Fetches and replies content from a MediaWiki-powered website."""
        reply = ''

        # First, fetch and parse the page
        tree, article, addr = self._get_article_tree(baseurl, search, use_mw_parsing=use_mw_parsing)

        # check if it gives a "Did you mean..." redirect
        didyoumean = tree.xpath('//div[@class="searchdidyoumean"]/a'
                                '[@title="Special:Search"]')
        if didyoumean:
            redirect = didyoumean[0].text_content().strip()
            if sys.version_info[0] < 3:
                if isinstance(redirect, unicode):
                    redirect = redirect.encode('utf-8','replace')
                if isinstance(search, unicode):
                    search = search.encode('utf-8','replace')
            if self.registryValue('showRedirects', msg.args[0]):
                reply += _('I didn\'t find anything for "%s". '
                           'Did you mean "%s"? ') % (search, redirect)

            tree, article, addr = self._get_article_tree(baseurl, didyoumean[0].get('href'))
            search = redirect

        # check if it's a page of search results (rather than an article), and
        # if so, retrieve the first result
        searchresults = tree.xpath('//div[@class="searchresults"]/ul/li/a') or \
            tree.xpath('//article/ul/li/a') # Special case for Wikia (2017-01-27)
        self.log.debug('Wikifetch: got search results %s', searchresults)

        if searchresults:
            redirect = searchresults[0].text_content().strip()
            if self.registryValue('showRedirects', msg.args[0]):
                reply += _('I didn\'t find anything for "%s", but here\'s the '
                           'result for "%s": ') % (search, redirect)
            # Follow the search result and fetch that article. Note: use the original
            # base url to prevent prefixes like "/wiki" from being added twice.
            self.log.debug('Wikifetch: following search result:')
            tree, article, addr = self._get_article_tree(None, searchresults[0].get('href'))
            search = redirect
        # otherwise, simply return the title and whether it redirected
        elif self.registryValue('showRedirects', msg.args[0]):
            redirect = re.search('\(%s <a href=[^>]*>([^<]*)</a>\)' %
                                 _('Redirected from'), article)
            if redirect:
                try:
                    redirect = tree.xpath('//span[@class="mw-redirectedfrom"]/a')[0]
                    redirect = redirect.text_content().strip()
                    title = tree.xpath('//*[@class="firstHeading"]')
                    title = title[0].text_content().strip()
                    if sys.version_info[0] < 3:
                        if isinstance(title, unicode):
                            title = title.encode('utf-8','replace')
                        if isinstance(redirect, unicode):
                            redirect = redirect.encode('utf-8','replace')
                    reply += '"%s" (Redirected from "%s"): ' % (title, redirect)
                except IndexError:
                    pass
        # extract the address we got it from - most sites have the perm link
        # inside the page itself
        try:
            addr = tree.find(".//link[@rel='canonical']").attrib['href']
        except (ValueError, AttributeError):
            self.log.debug('Wikifetch: failed <link rel="canonical"> link extraction, skipping')
            try:
                addr = tree.find(".//div[@class='printfooter']/a").attrib['href']
                addr = re.sub('([&?]|(amp;)?)oldid=\d+$', '', addr)
            except (ValueError, AttributeError):
                self.log.debug('Wikifetch: failed printfooter link extraction, skipping')
                # If any of the above post-processing tricks fail, just ignore
                pass

        # check if it's a disambiguation page
        disambig = tree.xpath('//table[@id="disambigbox"]') or \
            tree.xpath('//table[@id="setindexbox"]') or \
            tree.xpath('//div[contains(@class, "disambig")]')  # Wikia (2017-01-27)
        if disambig:
            reply += format(_('%u is a disambiguation page. '), addr)
            disambig = tree.xpath('//div[@id="bodyContent"]/div/ul/li')

            disambig_results = []
            for item in disambig:
                for link in item.findall('a'):
                    if link.text is not None:
                        # Hackishly bold all <a> tags
                        link.text = "&#x02;%s&#x02;" % link.text
                item = item.text_content().replace('&#x02;', '\x02')
                # Normalize and strip whitespace, to prevent newlines and such
                # from corrupting the display.
                item = utils.str.normalizeWhitespace(item).strip()
                disambig_results.append(item)
            if disambig_results:
                reply += format(_('Possible results include: %L'), disambig_results)

        # Catch talk pages
        elif 'ns-talk' in tree.find("body").attrib.get('class', ''):
            reply += format(_('This article appears to be a talk page: %u'), addr)
        else:
            if use_mw_parsing:
                # As of 2017-06-03, Wikipedia has put its text content under a new "mw-parser-output" div, while
                # other sites (e.g. Wikia) still have it directly under "mw-content-text".
                p = tree.xpath("//div[@id='mw-content-text']/p[1]") or tree.xpath("//div[@class='mw-parser-output']/p[1]")
            else: # Don't look for MediaWiki-specific tags if MediaWiki parsing is disabled
                p = tree.xpath("//p[1]")

            # Try to filter out navbars and other clutter by making sure that the
            # p tag we output has more words than the search query.
            search_wordcount = len(search.split())
            p = list(filter(lambda line: len(line.text_content().split()) > search_wordcount, p))

            if len(p) == 0 or 'wiki/Special:Search' in addr:
                if 'wikipedia:wikiproject' in addr.lower():
                    reply += format(_('This page appears to be a WikiProject page, '
                               'but it is too complex for us to parse: %u'), addr)
                else:
                    irc.error(_('Not found, or page malformed.'), Raise=True)
            else:
                p = p[0]
                # Replace <b> tags with IRC-style bold, this has to be
                # done indirectly because unescaped '\x02' is invalid in XML
                for b_tag in p.xpath('//b'):
                    b_tag.text = "&#x02;%s&#x02;" % (b_tag.text or '')
                p = p.text_content()
                p = p.replace('&#x02;', '\x02')
                # Get rid of newlines, etc., that can corrupt the output.
                p = utils.str.normalizeWhitespace(p)
                p = p.strip()
                if sys.version_info[0] < 3:
                    if isinstance(p, unicode):
                        p = p.encode('utf-8', 'replace')
                    if isinstance(reply, unicode):
                        reply = reply.encode('utf-8','replace')

                if not p:
                    reply = _('<Page was too complex to parse>')

                reply += format('%s %s %u', p, _('Retrieved from'), addr)
        reply = reply.replace('&amp;','&')

        # Remove inline citations (text[1][2][3], etc.)
        reply = re.sub('\[\d+\]', '', reply)

        return reply

    @internationalizeDocstring
    @wrap([getopts({'site': 'somethingWithoutSpaces',
                    'no-mw-parsing': ''}),
          'text'])
    def wiki(self, irc, msg, args, optlist, search):
        """[--site <site>] [--no-mw-parsing] <search term>

        Returns the first paragraph of a wiki article. Optionally, a --site
        argument can be given to override the default (usually Wikipedia) -
        try using '--site lyrics.wikia.com' or '--site wiki.archlinux.org'.

        If the --no-mw-parsing option is given, MediaWiki-specific parsing is
        disabled. This has the following effects:
          1) No attempt at searching for a relevant Wiki page is made, and
             an article with the same name as the search term is directly
             retrieved.
          2) The plugin will retrieve the first <p> tag found on a page,
             regardless of where it's found, and print it as text. This may
             not work on all sites, as some use <p> for navbars and headings
             as well.
        """
        optlist = dict(optlist)
        baseurl = optlist.get('site') or self.registryValue('url', msg.args[0])
        text = self._wiki(irc, msg, search, baseurl,
                          use_mw_parsing=not optlist.get('no-mw-parsing'),
                         )

        irc.reply(text)

    @internationalizeDocstring
    @wrap([additional('somethingWithoutSpaces')])
    def random(self, irc, msg, args, site):
        """[<site>]

        Returns the first paragraph of a random wiki article. Optionally, the 'site'
        argument can be given to override the default (usually Wikipedia)."""
        baseurl = site or self.registryValue('url', msg.args[0])
        text = self._wiki(irc, msg, 'Special:Random', baseurl)

        irc.reply(text)

Class = Wikifetch


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
