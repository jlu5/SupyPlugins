###
# Copyright (c) 2014-2017, James Lu
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
import unittest

class PkgInfoTestCase(PluginTestCase):
    plugins = ('PkgInfo',)
    if network:

        timeout = 12

        def testPkg(self):
            self.assertRegexp('pkg sid bash', 'Package: .*?bash .*?')
            self.assertRegexp('pkg trusty apt', 'Package: .*?apt .*?')
            self.assertNotError('pkg sid bash --depends')
            self.assertNotError('pkg sid vlc --source --depends')
            self.assertError('pkg afdsfsadf asfasfasf')
            self.assertError('pkg sid afsadfasfsa')

        def testVlist(self):
            self.assertError('vlist all afdsafas')
            self.assertError('vlist invalid-distro firefox')
            self.assertRegexp('vlist debian bash', 'Found [1-9][0-9]* '
                              'results: (.*?\(.*?\))+')

        @unittest.skip("Remote server is too unreliable (2017-02-23)")
        def testArchLinux(self):
            self.assertError('archlinux afdsfbjeiog')
            self.assertNotError('archlinux bash')
            self.assertRegexp('archlinux pacman --exact',
                              'Found 1.*?pacman')

        @unittest.skip("Remote server is too unreliable (2017-02-23)")
        def testArchAUR(self):
            self.assertRegexp('archaur yaourt', 'Found [1-9][0-9]* results:'
                              '.*?yaourt.*?')

        def testMintPkg(self):
            self.assertRegexp('linuxmint rebecca cinnamon', 'session')

        def testPkgsearch(self):
            self.assertRegexp('pkgsearch debian python', 'python')

        def testFilesearch(self):
            self.assertRegexp('filesearch sid supybot', 'limnoria')

        def testFedora(self):
            self.assertRegexp('fedora --release master bash*', 'bash')
            self.assertRegexp('fedora gnome-terminal', 'GNOME')
            # Not found queries that don't have any wildcards in them
            # should tell the user to try wrapping the search with *'s, since
            # Fedora's API always uses glob matches.
            self.assertRegexp('fedora sfasdfadsfasdfas', 'Try wrapping your query with \*')

        def testCentOS(self):
            self.assertRegexp('centos 7 os git-', 'git-all')
            self.assertRegexp('centos 6 os bash --arch i386', 'i686.rpm')
            self.assertNotError('centos 7 extras python')
            # This should be stripped.
            self.assertNotRegexp('centos 7 extras "a"', 'Parent Directory')

        def testFreeBSD(self):
            self.assertRegexp('freebsd lxterminal --exact', 'Found 1 result:.*?LXDE')
            self.assertNotError('freebsd bash')
            self.assertError('freebsd asdfasjkfalewrghaekglae')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
