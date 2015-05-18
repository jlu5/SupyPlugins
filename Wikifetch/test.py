###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
# Copyright (c) 2015, James Lu
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

class WikifetchTestCase(PluginTestCase):
    plugins = ('Wikifetch',)

    if network:
        def testWiki(self):
            self.assertRegexp('wiki Monty Python',
                              '\x02Monty Python\x02 \(sometimes known as \x02The Pythons\x02\)')
            self.assertRegexp('wiki roegdfjpoepo',
                              'Not found, or page malformed.*')

        def testDisambiguation(self):
            self.assertRegexp('wiki Python', 'is a disambiguation page.*'
                              'Possible results include:.*?,.*?,')
            self.assertRegexp('wiki Windows 3', '.*is a disambiguation page.*'
                              'Possible results include:.*?Windows 3.0.*?,.*?Windows 3.1x')

        def testWikiRedirects(self):
            # Via did you mean clause
            self.assertRegexp('wiki George Washingon',
                              'first President of the United States')
            # Via Search find-first-result snarfer
            self.assertRegexp('wiki synnero',
                              'A \x02synchro\x02 is')
            self.assertRegexp('wiki Foo', '"Foobar" \(Redirected from "Foo"\): '
                                          'The terms \x02foobar\x02')

        def testStripInlineCitations(self):
            self.assertNotRegexp('wiki UNICEF', '\[\d+\]')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
