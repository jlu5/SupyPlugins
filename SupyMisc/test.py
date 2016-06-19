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

from sys import version_info
from supybot.test import *

class SupyMiscTestCase(PluginTestCase):
    plugins = ('SupyMisc',)

    def setUp(self):
        PluginTestCase.setUp(self)
        self.prefix = 'foo!bar@baz.not'

    @unittest.skipUnless(network, "Network-based tests have been disabled via "
                         "--no-network")
    def testTld(self):
        self.assertNotError('tld .com')

    @unittest.skipUnless(network, "Network-based tests have been disabled via "
                         "--no-network")
    @unittest.skipIf(version_info[0] <= 2, "Doesn't work (raises UnicodeDecodeError) on Python 2.")
    def testTldInternationalTLDs(self):
        # https://www.iana.org/domains/root/db/xn--io0a7i
        # Chinese internationalized domain for 'network' (similar to .net)
        self.assertNotError('tld xn--io0a7i')
        self.assertNotError('tld \u7f51\u7edc')

    def testColorwheel(self):
        self.assertRegexp('colors', '.*\x03.*')

    def testHostFetchers(self):
        self.assertResponse('me', 'foo')
        self.assertResponse('getident', 'bar')
        self.assertResponse('gethost', 'baz.not')

    def testmreplace(self):
        self.assertResponse('mreplace hi,there hello,ok hmm, hi there everyone',
            'hmm, hello ok everyone')

    @unittest.skipUnless(network, "Network-based tests have been disabled via "
                         "--no-network")
    def testSPsourceFetch(self):
        self.assertNotError('supyplugins')
        self.assertRegexp('supyplugins SupyMisc/plugin.py', \
            '.*?blob\/master\/SupyMisc\/plugin\.py.*?')
        self.assertRegexp('supyplugins SupyMisc/', \
            '.*?tree\/master\/SupyMisc.*?')
        self.assertError('supyplugins asfswfuiahfawfawefawe')

    def testServerlist(self):
        self.assertNotError('serverlist')

    def testAverage(self):
        self.assertResponse('average 2 3 4', '3.0')
        self.assertResponse('average -5 6', '0.5')
        self.assertResponse('average 1337 -420 +42 +123456', '31103.75')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
