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
from HTMLParser import HTMLParser
import re
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PkgInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class PkgInfo(callbacks.Plugin):
    """Fetches package information from Debian and Ubuntu's websites."""
    threaded = True
    
    class DebPkgParse(HTMLParser):
    # Debian and Ubuntu are nice and give us meta tags in the beginning of the page!
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
            
    def DebianParse(self, irc, dist, pkg, distro=None):
        parser = PkgInfo.DebPkgParse()
        if distro == "debian" or dist.startswith(("oldstable","squeeze","wheezy","stable",
            "jessie","testing","sid","unstable")):
            baseurl = "http://packages.debian.org/"
        else:
            baseurl = "http://packages.ubuntu.com/"
        self.baseurl = baseurl
        self.url = baseurl + "{}/{}".format(dist, pkg)
        try:
            self.fd = utils.web.getUrl(self.url) 
        except Exception as e:
            irc.error(str(e), Raise=True)
        return parser.feed(self.fd)
        
    def package(self, irc, msg, args, dist, pkg):
        """<distribution> <package>
        
        Fetches information for <package> from Debian or Ubuntu's websites.
        <distribution> is the codename/release name (e.g. 'trusty', 'squeeze');
        the bot will automatically guess the distribution accordingly."""
        p = self.DebianParse(irc, dist.lower(),pkg.lower())
        if "Error</title>" in self.fd:
            err = re.findall("""<div class\="perror">\s*<p>(.*?)</p>$""", self.fd, re.M)
            if "two or more packages specified" in err[0]:
                irc.error("Unknown distribution/release.", Raise=True)
            irc.reply(err[0])
            return
        try:
            c = ' '.join(p[2].split("-"))
        except: c = p[2]
        # This <s>will</s>should return a list in the form [package description, distro,
        # release/codename, language (will always be 'en'), component, section, package-version]
        irc.reply("Package: \x02{} ({})\x02 in {} {} - {}; View more at: {}".format(pkg, p[-1], p[1], 
        c, p[0], self.url))
    package = wrap(package, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])

    def vlist(self, irc, msg, args, distro, pkg):
        """<distribution> <package>

        Fetches all available version of <package> in <distribution>, if such package exists."""
        versions = {}
        if distro.lower() == "ubuntu":
            suites = ['lucid', 'lucid-updates', 'lucid-backports', 'precise', 'precise-updates', 'precise-backports', 'raring', 'raring-updates', 'raring-backports', 'saucy', 'saucy-updates', 'saucy-backports', 'trusty', 'trusty-updates', 'trusty-backports', 'utopic']
        elif distro.lower() == "debian":
            suites = ['squeeze', 'squeeze-updates', 'squeeze-backports', 'squeeze-backports-sloppy', 'wheezy', 'wheezy-updates', 'wheezy-backports', 'jessie', 'sid', 'experimental']
        else: irc.error("Unknown distribution/release.", Raise=True)
        for su in suites:
            p = self.DebianParse(irc, su, pkg.lower(), distro.lower())
            if "Error</title>" not in self.fd:
                # make a dict in the form {suite:version}
                versions[p[2]] = p[-1]
        if not versions:
            irc.error("No results found.", Raise=True)
        s = "Found {} results:".format(len(versions))
        for v in versions.keys():
            s += " {} \x02({})\x02,".format(v, versions[v])
        s += " View more at: {}search?keywords={}".format(self.baseurl, pkg)
        irc.reply(s)
    vlist = wrap(vlist, ['somethingWithoutSpaces', 'somethingWithoutSpaces'])


Class = PkgInfo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
