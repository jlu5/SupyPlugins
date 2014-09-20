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
from collections import OrderedDict, defaultdict
try:
	from urllib.parse import urlencode
except ImportError:
	from urllib import urlencode
import json
import re
try:
    from HTMLParser import HTMLParser
except ImportError:
	from html.parser import HTMLParser
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PkgInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class PkgInfo(callbacks.Plugin):
    """Fetches package information from the repositories of 
    Debian, Arch Linux, and Ubuntu."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(PkgInfo, self)
        self.__parent.__init__(irc)
        self.addrs = {'ubuntu':'http://packages.ubuntu.com/',
                      'debian':"http://packages.debian.org/"}

    class DebPkgParse(HTMLParser):
        def handle_starttag(self, tag, attrs):
            if tag == "meta":
                attrs = dict(attrs)
                try:
                    if attrs['name'] == "Description":
                        self.tags.append(attrs['content'])
                    elif attrs['name'] == "Keywords":
                        self.tags.extend(attrs['content'].replace(",","").split())
                except KeyError: pass
        def feed(self, data):
            self.tags = []
            HTMLParser.feed(self, data)
            return self.tags

    def DebianParse(self, irc, suite, pkg, distro):
        parser = PkgInfo.DebPkgParse()
        self.url = self.addrs[distro] + "{}/{}".format(suite, pkg)
        try:
            self.fd = utils.web.getUrl(self.url).decode("utf-8")
        except Exception as e:
            irc.error(str(e), Raise=True)
        return parser.feed(self.fd)

    def MadisonParse(self, pkg, dist, codenames='', suite=''):
        arch = ','.join(self.registryValue("archs"))
        self.arg = urlencode({'package':pkg,'table':dist,'a':arch,'c':codenames,'s':suite})
        url = 'http://qa.debian.org/madison.php?text=on&' + self.arg
        d = OrderedDict()
        fd = utils.web.getUrlFd(url)
        for line in fd.readlines():
            L = line.decode("utf-8").split("|")
            d[L[2].strip()] = (L[1].strip(),L[3].strip())
        if d:
            if self.registryValue("verbose"):
                return 'Found %s results: ' % len(d) + ', '.join("{!s} " \
                "\x02({!s} [{!s}])\x02".format(k,v[0],v[1]) for (k,v) in \
                d.items())
            return 'Found %s results: ' % len(d) + ', '.join("{!s} " \
            "\x02({!s})\x02".format(k,v[0]) for (k,v) in d.items())
        
    def package(self, irc, msg, args, suite, pkg):
        """<suite> <package>
        
        Fetches information for <package> from Debian or Ubuntu's repositories.
        <suite> is the codename/release name (e.g. 'trusty', 'squeeze').
        For Arch Linux packages, please use 'archpkg' and 'archaur' instead."""
        # Guess the distro from the suite name
        if suite.startswith(("oldstable","squeeze","wheezy","stable",
            "jessie","testing","sid","unstable")):
            distro = "debian"
        else: distro = "ubuntu"
        p = self.DebianParse(irc, suite.lower(), pkg.lower(), distro)
        if "Error</title>" in self.fd:
            err = re.findall("""<div class\="perror">\s*<p>(.*?)</p>$""", self.fd, re.M)
            if "two or more packages specified" in err[0]:
                irc.error("Unknown distribution/release.", Raise=True)
            irc.reply(err[0])
            return
        try:
            c = ' '.join(p[2].split("-"))
        except: c = p[2]
        # This returns a list in the form [package description, distro,
        # release/codename, language (will always be 'en'), component, section, package-version]
        irc.reply("Package: \x02{} ({})\x02 in {} {} - {}; View more at: {}".format(pkg, p[-1], p[1],
        c, p[0], self.url))
    package = wrap(package, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])

    def vlist(self, irc, msg, args, distro, pkg):
        """<distribution> <package>

        Fetches all available version of <package> in <distribution>, if 
        such package exists. Supported entries for <distribution> 
        include: 'debian', 'ubuntu', 'derivatives', and 'all'."""
        distro = distro.lower()
        d = self.MadisonParse(pkg, distro)
        if not d: irc.error("No results found.",Raise=True)
        try:
            d += " View more at: {}search?keywords={}".format(self.addrs[distro], pkg)
        except KeyError: pass
        irc.reply(d)
    vlist = wrap(vlist, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])
    
    def archpkg(self, irc, msg, args, pkg, opts):
        """<package> [--glob]
        
        Looks up <package> in the Arch Linux package repositories.
        If --glob is given, the bot will search for <package> as a glob 
        instead of the exact package name. However, this often has the
        problem of giving many irrelevant results (e.g. 'git' will also
        match 'di git al'."""
        baseurl = 'http://www.archlinux.org/packages/search/json/?'
        if 'glob' in dict(opts):
            fd = utils.web.getUrl(baseurl + urlencode({'q':pkg}))
        else:
            fd = utils.web.getUrl(baseurl + urlencode({'name':pkg}))
        data = json.loads(fd.decode("utf-8"))
        if data['valid'] and data['results']:
            f = set()
            archs = defaultdict(list)
            for x in data['results']:
                s = "{} - {} \x02({})\x02".format(x['pkgname'],x['pkgdesc'],x['pkgver'])
                f.add(s)
                archs[s].append(x['arch'])
            if self.registryValue("verbose"):
                irc.reply('Found %s results: ' % len(f)+', ' \
                .join("{} \x02[{!s}]\x02".format(s, ', '.join(archs[s])) for s in f))
            else:
                irc.reply('Found {} results: {}'.format(len(f),', '.join(f)))
        else: irc.error("No results found.",Raise=True)
    archpkg = wrap(archpkg, ['somethingWithoutSpaces', getopts({'glob':''})])
    
    def archaur(self, irc, msg, args, pkg):
        """<package>
        
        Looks up <package> in the Arch Linux AUR."""
        baseurl = 'https://aur.archlinux.org/rpc.php?type=search&'
        fd = utils.web.getUrl(baseurl + urlencode({'arg':pkg}))
        data = json.loads(fd.decode("utf-8"))
        if data["type"] == "error":
            irc.error(data["results"], Raise=True)
        if data['resultcount']:
            s = "Found {} result{}: ".format(data["resultcount"], 
                's' if data["resultcount"] != 1 else '')
            for x in data['results']:
                verboseInfo = ''
                if self.registryValue("verbose"):
                    verboseInfo = " [ID:{} Votes:{}]".format(x['ID'], x['NumVotes'])
                s += "{} - {} \x02({}{})\x02, ".format(x['Name'],x['Description'],x['Version'], verboseInfo)
            irc.reply(s[:-2])
        else: irc.error("No results found.",Raise=True)
    archaur = wrap(archaur, ['somethingWithoutSpaces'])


Class = PkgInfo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
