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

        def test_pkg_debian(self):
            self.assertNotError('pkg sid bash')
            self.assertNotError('pkg sid bash --depends')
            self.assertNotError('pkg sid ffmpeg --source')
            self.assertNotError('pkg sid vlc --source --depends')
            self.assertError('pkg unittestinvaliddistignore unittestinvalidpackageignore')
            self.assertError('pkg sid unittestinvalidpackageignore')
            self.assertNotError('pkgsearch debian python')

        def test_pkg_ubuntu(self):
            self.assertNotError('pkg xenial apt')
            self.assertNotError('pkg xenial python3 --depends')
            self.assertNotError('pkg xenial ubuntu-meta --source')
            self.assertNotError('pkg xenial ubuntu-meta --source --depends')
            self.assertNotError('pkgsearch ubuntu gtk')

        def test_vlist(self):
            self.assertNotError('vlist debian bash')
            self.assertNotError('vlist ubuntu variety')
            self.assertError('vlist all unittestinvalidpackageignore')
            self.assertError('vlist invalid-distro firefox')

        #@unittest.skip("Remote server is too unreliable (2017-02-23)")
        def test_pkg_arch(self):
            self.assertNotError('pkg arch audacity')
            self.assertNotError('pkgsearch arch ffmpeg')
            self.assertError('pkg arch unittestinvalidpackageignore')
            self.assertError('pkgsearch arch unittestinvalidpackageignore')

        #@unittest.skip("Remote server is too unreliable (2017-02-23)")
        def test_pkg_archaur(self):
            self.assertNotError('pkg archaur yaourt')
            self.assertNotError('pkgsearch archaur yaourt')
            self.assertError('pkg archaur unittestinvalidpackageignore')
            self.assertError('pkgsearch archaur unittestinvalidpackageignore')

        def test_pkg_mint(self):
            self.assertNotError('pkgsearch sonya cinnamon')
            self.assertNotError('pkg sonya cinnamon')
            self.assertError('pkg mint unittestinvalidpackageignore')
            self.assertError('pkgsearch mint unittestinvalidpackageignore')

        def test_pkg_freebsd(self):
            self.assertNotError('pkg freebsd lxterminal')
            self.assertNotError('pkgsearch freebsd gnome')
            self.assertRegexp('pkg freebsd python3 --depends', 'python3.*?requires')
            self.assertError('pkg freebsd unittestinvalidpackageignore')
            self.assertError('pkgsearch freebsd unittestinvalidpackageignore')

        def test_pkg_fedora(self):
            self.assertNotError('pkg fedora gnome-shell')

        def test_pkg_gentoo(self):
            self.assertNotError('pkg gentoo www-client/firefox')
            self.assertRegexp('pkgsearch gentoo lightdm', 'lightdm-gtk')

        def test_filesearch(self):
            self.assertRegexp('filesearch sid supybot', 'limnoria')

        def test_centos(self):
            self.assertRegexp('centos 7 os git-', 'git-all')
            self.assertRegexp('centos 6 os bash --arch i386', 'i686.rpm')
            self.assertNotError('centos 7 extras python')
            # This should be stripped.
            self.assertNotRegexp('centos 7 extras "a"', 'Parent Directory')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
