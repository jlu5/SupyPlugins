# -*- coding: utf-8 -*-
###
# Copyright (c) 2023 James Lu
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
import unittest

from . import formatter

from supybot.test import *

class WikifetchFormatterTest(unittest.TestCase):
    def assertFormatEqual(self, wikitext, expected, **kwargs):
        output = formatter.fmt(wikitext, **kwargs)
        self.assertEqual(output, expected)

    def test_basic(self):
        self.assertFormatEqual('', '')
        self.assertFormatEqual(
            'The quick brown fox jumps over the lazy dog',
            'The quick brown fox jumps over the lazy dog')

    def test_format_tags(self):
        self.assertFormatEqual(
            "'''Lorem ipsum''' dolor sit amet, consectetur adipiscing elit",
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit")
        self.assertFormatEqual(
            "Test '''bold''' and ''italics'' and '''''both'''''.",
            "Test bold and italics and both.")

    def test_format_wikilinks(self):
        self.assertFormatEqual(
            "Abc [[def ghi]]", "Abc def ghi")
        self.assertFormatEqual(
            "Abc [[def|custom title]]  xyz", "Abc custom title  xyz")
        # namespaced links get dropped
        self.assertFormatEqual(
            "hello world [[File:test.jpg]]", "hello world")
        self.assertFormatEqual(
            "[[Special:RecentChanges]]   [[en:Test]]", "")

    def test_format_images(self):
        self.assertFormatEqual(
            "[[File:Foo.png|foo]]\nsome text",
            "some text", summary=True)
        self.assertFormatEqual(
            "[[File:Foo.png|foo]]\n\nsome text again",
            "some text again")

        # Adapted from https://en.wikipedia.org/wiki/Wikipedia:Extended_image_syntax#Examples
        self.assertFormatEqual("""text text text
[[File:Westminstpalace.jpg|150px|alt=A large clock tower and other buildings line a great river.|The Palace of Westminster]]
aa bb cc dd
[[File:tst.png|100px|alt=Tiny globe|This is a globe.]]
eee fff""", "text text text\n\naa bb cc dd\n\neee fff")
        self.assertFormatEqual("""[[File:Westminstpalace.jpg|150px|alt=A large clock tower and other buildings line a great river.|The Palace of Westminster]]
aa bb cc dd
[[File:tst.png|100px|alt=Tiny globe|This is a globe.]]
eee fff""", "aa bb cc dd", summary=True)

    def test_format_external_links(self):
        self.assertFormatEqual(
            "first [http://example.com] last", "first http://example.com last")
        self.assertFormatEqual(
            "first [http://example.com second] last", "first second last")

    def test_format_templates(self):
        # Templates are ignored
        self.assertFormatEqual(
            "{{tmpl|arg=12345}}", "")
        self.assertFormatEqual(
            "{{tmpl2|foo=12345|bar=abcdefg}} test", "test")
        self.assertFormatEqual(
            "{{outer|{{inner test}}}}", "")
        # mwparserfromhell usage example
        self.assertFormatEqual(
            "{{cleanup}} '''Foo''' is a [[bar]]. {{uncategorized}}",
            "Foo is a bar.")

    # multiline
    def test_multiline(self):
        self.assertFormatEqual(
            "Hello world.\n\nThis is the second line.",
            "Hello world.\n\nThis is the second line.")
        self.assertFormatEqual(
            "Hello world.\n\nThis is the second line.",
            "Hello world.", summary=True)
        self.assertFormatEqual(
            "This sentence is on one\nline.\n\n2nd line",
            "This sentence is on one\nline.", summary=True)

        self.assertFormatEqual(
            "\n\n\n    Leading spaces are dropped.\n\nThis is the second line.",
            "Leading spaces are dropped.\n\nThis is the second line.")
        self.assertFormatEqual(
            "\n\n\n    Leading spaces are dropped.\n\nThis is the second line.",
            "Leading spaces are dropped.", summary=True)

    def test_multiline_drop_empty_lines(self):
        # drop lines that are empty after filtering
        # e.g. Arch Linux Wiki pages with cross-language links
        self.assertFormatEqual(
            "[[Category:abcd]]\n[[de:Test]]\n[[en:Test]]\n[[zh:Test]]\n{{Related articles start}}\n"
            "Now the actual content starts\n1 2 3 4 5 6",
            "Now the actual content starts\n1 2 3 4 5 6", summary=True)
        self.assertFormatEqual(
            "[[Category:abcd]]\n\n {{Related articles start}} \n\n[[Help:abcdef]]\n\n"
            "Now the actual content starts\n\n1 2 3 4 5 6",
            "Now the actual content starts", summary=True)

    def test_cleanup(self):
        # drop lines that are empty after filtering
        # e.g. Arch Linux Wiki pages with cross-language links
        empty_parens_after_filtering = """'''Vancouver''' ({{IPAc-en|audio=EN-Vancouver.ogg|v|æ|n|ˈ|k|uː|v|ər}}
        {{respell|van|KOO|vər}}) is a major city in [[western Canada]],"""
        self.assertFormatEqual(
            empty_parens_after_filtering,
            "Vancouver is a major city in western Canada,", summary=True)

if network:
    class Wikipedia(PluginTestCase):
        plugins = ('Wikifetch',)

        def testWikipedia(self):
            self.assertRegexp('wiki Vancouver',
                              r'^Vancouver.*Canada')
            self.assertRegexp('wiki Python (programming language)',
                              'Python.*programming language')

        def testWikipediaFollowRedirects(self):
            self.assertRegexp('wiki CYVR',
                              'Vancouver International Airport')

        def testWikipediaSearch(self):
            self.assertRegexp('wiki Python language',
                              'Python.*programming language')

        def testWikipediaLang(self):
            self.assertRegexp('wiki --lang fr Paris', 'Paris.*capitale')

            with conf.supybot.plugins.Wikifetch.Wikipedia.lang.context('zh'):
                self.assertRegexp('wiki 地球', '地球.*太阳系')

        def testFandom(self):
            self.assertRegexp('fandom minecraft Ender Dragon',
                              r'[Ee]nder [Dd]ragon.*boss')

            self.assertRegexp('fandom warframe Warframe', r'[Ww]arframe')

        def testWikigg(self):
            self.assertRegexp('wikigg terraria Ocean',
                              r'Ocean.*biome')

        def testCustomArchWiki(self):
            self.assertRegexp('customwiki https://wiki.archlinux.org/api.php KDE',
                              r'KDE is.*desktop')

        def testCustomParadoxWikis(self):
            # api.php will be appended if not present
            self.assertRegexp('customwiki https://skylines.paradoxwikis.com/ Zoning',
                              r'Zones.*buildings')
