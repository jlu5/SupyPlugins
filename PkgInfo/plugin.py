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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from collections import OrderedDict
import urllib
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PkgInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class PkgInfo(callbacks.Plugin):
    """Fetches package information from Debian and Ubuntu's repositories."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(PkgInfo, self)
        self.__parent.__init__(irc)
        self.addrs = {'ubuntu':'http://packages.ubuntu.com/',
                      'debian':"http://packages.debian.org/"}

    def MadisonParse(self, pkg, dist, codenames='', suite=''):
        arch = ','.join(self.registryValue("archs"))
        self.arg = urllib.urlencode({'package':pkg,'table':dist,'a':arch,'c':codenames,'s':suite})
        url = 'http://qa.debian.org/madison.php?text=on&' + self.arg
        d = OrderedDict()
        fd = utils.web.getUrlFd(url)
        for line in fd.readlines():
            L = line.split("|")
            d[L[2].strip()] = (L[1].strip(),L[3].strip())
        if d:
            if self.registryValue("showArchs"):
                return 'Found %s results: ' % len(d) + ', '.join("{!s} " \
                "\x02({!s} [{!s}])\x02".format(k,v[0],v[1]) for (k,v) in \
                d.items())
            return 'Found %s results: ' % len(d) + ', '.join("{!s} " \
            "\x02({!s})\x02".format(k,v[0]) for (k,v) in d.items())
        
    def package(self, irc, msg, args, suite, pkg):
        """<suite> <package>
        
        Fetches information for <package> from Debian or Ubuntu's repositories.
        <suite> is the codename/release name (e.g. 'trusty', 'squeeze')."""
        d = self.MadisonParse(pkg, 'all', suite=suite)
        if not d: irc.error("No results found.")
        try:
            d += " View more at: http://qa.debian.org/madison.php?{}".format(self.arg)
        except KeyError: pass
        irc.reply(d)
    package = wrap(package, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])

    def vlist(self, irc, msg, args, distro, pkg):
        """<distribution> <package>

        Fetches all available version of <package> in <distribution>, if 
        such package exists. Supported entries for <distribution> 
        include: 'debian', 'ubuntu', 'derivatives', and 'all'."""
        distro = distro.lower()
        d = self.MadisonParse(pkg, distro)
        if not d: irc.error("No results found.")
        try:
            d += " View more at: {}search?keywords={}".format(self.addrs['distro'], pkg)
        except KeyError: pass
        irc.reply(d)
    vlist = wrap(vlist, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])


Class = PkgInfo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
