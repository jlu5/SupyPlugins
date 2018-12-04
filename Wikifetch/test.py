# -*- coding: utf-8 -*-
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

from supybot.test import *

if network:
    class Wikipedia(PluginTestCase):
        plugins = ('Wikifetch',)

        def testWikipedia(self):
            self.assertRegexp('wiki Monty Python',
                              r'\x02Monty Python\x02.*?\.')
            self.assertRegexp('wiki roegdfjpoepo',
                              'Not found, or page malformed.*')

        def testStripInlineCitations(self):
            self.assertNotRegexp('wiki UNICEF', '\[\d+\]')

        def testIgnoreCoordinates(self):
            # Articles for countries, cities, landmarks, etc. have GPS coordinates added to the top right.
            # These should be ignored because we want to focus on the actual article text.
            self.assertNotRegexp('wiki Canada', 'Coordinates\:')
            self.assertNotRegexp('wiki Eiffel Tower', 'Coordinates\:')
            self.assertNotRegexp('wiki Poland', 'Coordinates\:')

        def testDisambig(self):
            self.assertRegexp('wiki Python', 'is a disambiguation page.*'
                              'Possible results include:.*?Pythonidae.*?;.*?;')
            self.assertRegexp('wiki Windows 3', '.*is a disambiguation page.*'
                              'Possible results include:.*?Windows 3.0.*?;.*?Windows 3.1x')

        def testDisambigStripSpaces(self):
            self.assertNotRegexp('wiki Na', '\n')

        def testArticlesWithSymbolsInName(self):
            self.assertNotError('wiki /')
            self.assertNotError('wiki *')
            self.assertNotError('wiki GNU/Linux')
            self.assertNotError('wiki --site en.wikipedia.org /')

        def testRedirects(self):
            self.assertRegexp('wiki Foo', '"Foobar" \(Redirected from "Foo"\): '
                                          'The terms \x02foobar\x02')

        def testWikiBold(self):
            self.assertRegexp('wiki Apple', '\x02')
            # Complex combination of the <a> tag inside a <b> tag; we should always use
            # empty bold content instead of the text "None".
            self.assertNotRegexp('wiki Fallstreak hole', 'None')

        def testWikiRandom(self):
            self.assertNotError('random')

        def testSiteCombinations(self):
            self.assertNotError('wiki --site en.wikipedia.org Bread')
            self.assertNotError('wiki --site EN.WikiPedia.Org Bread')  # god forbid if anyone actually types like this
            self.assertNotError('wiki --site http://en.wikipedia.org/ Bread')
            self.assertNotError('wiki --site en.wikipedia.org/wiki Bread')
            self.assertNotError('wiki --site https://en.wikipedia.org Bread')
            self.assertNotError('wiki --site https://en.wikipedia.org/wiki Bread')

        def testNonEnglishWikipedia(self):
            self.assertNotError('wiki --site fr.wikipedia.org Paris')
            self.assertNotError('wiki --site de.wikipedia.org Berlin')
            self.assertNotError('wiki --site zh.wikipedia.org 中文')
            self.assertNotError('wiki --site ar.wikipedia.org 2017')

    class Wikia(PluginTestCase):
        plugins = ('Wikifetch',)

        def testWikia(self):
            self.assertNotError('wiki --site help.wikia.com Help:Wikitext')

        def testWikiaDisambig(self):
            self.assertRegexp('wiki --site danball.wikia.com Fire', '.*?disambiguation.*?')

    class ArchLinuxWiki(PluginTestCase):
        plugins = ('Wikifetch',)

        def testArchWiki(self):
            self.assertNotError('wiki --site wiki.archlinux.org Bash')

    class GentooWiki(PluginTestCase):
        plugins = ('Wikifetch',)

        def testGentooWiki(self):
            self.assertNotError('wiki --site wiki.gentoo.org OpenRC')

    class WikimediaSites(PluginTestCase):
        plugins = ('Wikifetch',)

        def testMediaWiki(self):
            self.assertNotError('wiki --site mediawiki.org Sites using MediaWiki')

        def testWikimediaCommons(self):
            self.assertNotError('wiki --site commons.wikimedia.org America')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
