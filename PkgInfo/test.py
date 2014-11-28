###
# Copyright (c) 2014, James Lu
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
from supybot.test import *

class PkgInfoTestCase(PluginTestCase):
    plugins = ('PkgInfo',)
    def testPkgCommand(self):
        self.assertRegexp('pkg sid bash', 'Package: .*?bash'
        ' .*?')
        self.assertRegexp('pkg trusty apt', 'Package: .*?apt'
        ' .*?')
        self.assertError('pkg afdsfsadf asfasfasf')
        self.assertRegexp('pkg sid afsadfasfsa', 'no such package', re.I)

    def testVlistCommandBasics(self):
        self.assertError('vlist all afdsafas')
        self.assertError('vlist invalid-distro firefox')
        self.assertRegexp('vlist debian bash', 'Found [1-9][0-9]* results: (.*?\(.*?\))+')
        self.assertRegexp('vlist debian bash --source', 'Found [1-9][0-9]* results: .*?: bash.*?\(.*?\).*?')

    def testArchpkg(self):
        self.assertError('archpkg afdsfbjeiog')
        try:
            self.assertNotError('archpkg bash')
            self.assertRegexp('archpkg pacman --exact', 'Found 1.*?pacman -.*?')
        except AssertionError as e:
            if "HTTP Error 50" in str(e): # It's not our fault; the API is down.
                raise unittest.SkipTest("HTTP error 50x; the API's probably down again")

    def testArchaur(self):
        self.assertError('archaur wjoitgjwotgjv')
        self.assertRegexp('archaur yaourt', 'Found [1-9][0-9]* results: .*?yaourt.*?')

    def testMintPkg(self):
        self.assertNotError('mintpkg qiana cinnamon')

    def testPkgsearch(self):
        self.assertNotError('pkgsearch debian python')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
