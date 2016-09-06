###
# Copyright (c) 2014-2016, James Lu
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

from __future__ import unicode_literals
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.log as log

from collections import OrderedDict, defaultdict
try:  # Python 3
    from urllib.parse import urlencode, quote
except ImportError:  # Python 2
    from urllib import urlencode, quote
import json
import re
try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Beautiful Soup 4 is required for this plugin: get it"
                      " at http://www.crummy.com/software/BeautifulSoup/bs4/"
                      "doc/#installing-beautiful-soup")

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PkgInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class MadisonParser():
    def parse(self, pkg, dist, archs, codenames='', suite='', reverse=False, verbose=False):
        """Parser for the madison API at https://qa.debian.org/madison.php."""
        # This arch value implies 'all' (architecture-independent packages)
        # and 'source' (source packages), in order to prevent misleading
        # "Not found" errors.
        self.arg = {'package': pkg, 'table': dist, 'a': archs, 'c': codenames,
                    's': suite}
        self.arg = urlencode(self.arg)
        url = 'https://qa.debian.org/madison.php?text=on&' + self.arg
        log.debug("PkgInfo: Using url %s for 'vlist' command", url)
        d = OrderedDict()
        fd = utils.web.getUrlFd(url)
        for line in fd.readlines():
            L = line.decode("utf-8").split("|")
            try:
                L = map(unicode.strip, L)
            except:
                L = map(str.strip, L)
            name, version, release, archs = L
            d[release] = (version, archs)
        if d:
            if reverse:
                # *sigh*... I wish there was a better way to do this
                d = OrderedDict(reversed(tuple(d.items())))
            if verbose:
                items = ["{name} \x02({version} [{archs}])\x02".format(name=k,
                         version=v[0], archs=v[1]) for (k, v) in d.items()]
            else:
                items = ["{name} \x02({version})\x02".format(name=k,
                         version=v[0]) for (k, v) in d.items()]
            s = format('Found %n: %L', (len(d), 'result'), items)
            return s
        else:
            log.debug("PkgInfo: No results found for URL %s", url)

unknowndist = _("Unknown distribution. This command only supports "
                "package lookup for Debian and Ubuntu. For a list of"
                "commands for other distros' packages, use "
                "'list PkgInfo'.")
addrs = {'ubuntu': 'http://packages.ubuntu.com/',
         'debian': 'https://packages.debian.org/',
         # This site is very, VERY slow, but it still works..
         'debian-archive': 'http://archive.debian.net/'}
_normalize = lambda text: utils.str.normalizeWhitespace(text).strip()

def _getDistro(release):
    """<release>

    Guesses the distribution from the release name."""
    release = release.lower()
    debian = ("oldoldstable", "oldstable", "wheezy", "stable",
              "jessie", "testing", "sid", "unstable", "stretch", "buster",
              "experimental")
    debian_archive = ("bo", "hamm", "slink", "potato", "woody", "sarge",
                      "etch", "lenny", "squeeze")
    ubuntu = ("precise", "trusty", "wily", "xenial", "yakkety")
    if release.startswith(debian):
        return "debian"
    elif release.startswith(ubuntu):
        return "ubuntu"
    elif release.startswith(debian_archive):
        return "debian-archive"

class PkgInfo(callbacks.Plugin):
    """Fetches package information from the repositories of
    Arch Linux, CentOS, Debian, Fedora, FreeBSD, Linux Mint, and Ubuntu."""
    threaded = True

    _deptypes = ['dep', 'rec', 'sug', 'enh', 'adep', 'idep']
    _dependencyColor = utils.str.MultipleReplacer({'rec:': '\x0312rec:\x03',
                                                   'dep:': '\x0304dep:\x03',
                                                   'sug:': '\x0309sug:\x03',
                                                   'adep:': '\x0305adep:\x03',
                                                   'idep:': '\x0302idep:\x03',
                                                   'enh:': '\x0308enh:\x03'})
    def package(self, irc, msg, args, release, pkg, opts):
        """<release> <package> [--depends] [--source]

        Fetches information for <package> from Debian or Ubuntu's repositories.
        <release> is the codename/release name (e.g. 'trusty', 'squeeze'). If
        --depends is given, fetches dependency info for <package>. If --source
        is given, look up the source package instead of a binary."""
        pkg = pkg.lower()
        distro = _getDistro(release)
        opts = dict(opts)
        source = 'source' in opts
        try:
            url = addrs[distro]
        except KeyError:
            irc.error(unknowndist, Raise=True)
        if source:  # Source package was requested
            url += 'source/'
        url += "{}/{}".format(release, pkg)

        try:
            text = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)

        # Workaround unescaped << in package versions (e.g. "python (<< 2.8)") not being parsed
        # correctly.
        text = text.replace('<<', '&lt;&lt;')

        soup = BeautifulSoup(text)

        if "Error" in soup.title.string:
            err = soup.find('div', attrs={"id": "content"}).find('p').string
            if "two or more packages specified" in err:
                irc.error("Unknown distribution/release.", Raise=True)
            irc.reply(err)
            return

        # If we're using the --depends option, handle that separately.
        if 'depends' in opts:
            items = soup.find('div', {'id': 'pdeps'}).find_all('dt')
            # Store results by type and name, but in an ordered fashion: show dependencies first,
            # followed by recommends, suggests, and enhances.
            res = OrderedDict((deptype+':', []) for deptype in self._deptypes)
            for item in items:
                # Get package name and related versions and architectures:
                # <packagename> (>= 1.0) [arch1, arch2]
                try:
                    deptype = item.span.text if item.find('span') else ''
                    if deptype not in res:
                        continue  # Ignore unsupported fields

                    name = '%s %s' % (ircutils.bold(item.a.text),
                            item.a.next_sibling.replace('\n', '').strip())
                    name = utils.str.normalizeWhitespace(name).strip()
                    if item.find('span'):
                        res[deptype].append(name)
                    else:
                        # OR dependency; format accordingly
                        res[deptype][-1] += " or %s" % name
                except AttributeError:
                    continue

            if res:
                s = format("Package \x02%s\x02 dependencies: ", pkg)
                for deptype, packages in res.items():
                    if packages:
                        deptype = self._dependencyColor(deptype)
                        s += format("%s %L; ", deptype, packages)
                s += format("%u", url)

                irc.reply(s)

            else:
                irc.error("%s doesn't seem to have any dependencies." % pkg)
            return

        desc = soup.find('meta', attrs={"name": "Description"})["content"]

        # Override description if we selected source lookup, since the meta
        # tag Description should be empty for those. Replace this with a list
        # of binary packages that the source package builds.
        if source:
            binaries = soup.find('div', {'id': "pbinaries"})
            binaries = [ircutils.bold(obj.a.text) for obj in binaries.find_all('dt')]
            desc = format('Built packages: %L', binaries)

        # Get package information from the meta tags
        keywords = soup.find('meta', attrs={"name": "Keywords"})["content"]
        keywords = keywords.replace(",", "").split()
        version = keywords[-1]

        # Handle virtual packages by showing a list of packages that provide it
        if version == "virtual":
            providing = [ircutils.bold(obj.a.text) for obj in soup.find_all('dt')]
            desc = "Virtual package provided by: %s" % ', '.join(providing[:10])
            if len(providing) > 10:
                desc += " and %s others" % (ircutils.bold(len(providing) - 10))
        s = format("Package: \x02%s (%s)\x02 in %s - %s, View more at: %u",
                   pkg, version, keywords[1], desc, url)
        irc.reply(s)
    pkg = wrap(package, ['somethingWithoutSpaces', 'somethingWithoutSpaces',
               getopts({'depends': '', 'source': ''})])

    def vlist(self, irc, msg, args, distro, pkg, opts):
        """<distribution> <package> [--reverse]

        Fetches all available version of <package> in <distribution>, if
        such package exists. Supported entries for <distribution>
        include 'debian', 'ubuntu', 'derivatives', and 'all'. If
        --reverse is given, show the newest package versions first."""
        pkg, distro = map(str.lower, (pkg, distro))
        supported = ("debian", "ubuntu", "derivatives", "all")
        if distro not in supported:
            distro = _getDistro(distro)
            if distro is None:
                irc.error(unknowndist, Raise=True)
        opts = dict(opts)
        reverse = 'reverse' in opts
        archs = self.registryValue("archs") + ['all', 'source']
        archs = ','.join(set(archs))
        parser = MadisonParser()
        d = parser.parse(pkg, distro, archs, reverse=reverse,
                         verbose=self.registryValue("verbose"))
        if not d:
            irc.error("No results found.", Raise=True)
        try:
            url = "{}search?keywords={}".format(addrs[distro], pkg)
            d += format("; View more at: %u", url)
        except KeyError:
            pass
        irc.reply(d)
    vlist = wrap(vlist, ['somethingWithoutSpaces', 'somethingWithoutSpaces',
                 getopts({'reverse': ''})])

    def archlinux(self, irc, msg, args, pkg, opts):
        """<package> [--exact]

        Looks up <package> in the Arch Linux package repositories.
        If --exact is given, will output only exact matches.
        """
        pkg = pkg.lower()

        if 'exact' in dict(opts):
            encoded = urlencode({'name': pkg})
        else:
            encoded = urlencode({'q': pkg})

        url = 'https://www.archlinux.org/packages/search/json/?' + encoded
        friendly_url = 'https://www.archlinux.org/packages/?' + encoded

        self.log.debug("PkgInfo: using url %s for 'archlinux' command", url)

        fd = utils.web.getUrl(url)
        data = json.loads(fd.decode("utf-8"))

        if data['valid'] and data['results']:
            # We want one entry per package, but the API gives one
            # entry per architecture! Remove duplicates with a set:
            results = set()

            # For each package, store the available architectures as
            # a list.
            archs = defaultdict(list)
            for pkgdata in data['results']:
                # Expand the package data dict into arguments for formatting
                s = "\x02{pkgname}\x02 - {pkgdesc} \x02({pkgver})\x02".format(**pkgdata)

                if self.registryValue("verbose"):
                    # In verbose mode, also show the repo the package is in.
                    s += " [\x02%s\x02]" % pkgdata['repo']

                results.add(s)
                archs[s].append(pkgdata['arch'])

            irc.reply(format('Found %n: %L; View more at %u',
                             (len(results), 'result'), sorted(results),
                             friendly_url))
        else:
            irc.error("No results found.", Raise=True)
    archlinux = wrap(archlinux, ['somethingWithoutSpaces', getopts({'exact': ''})])

    def archaur(self, irc, msg, args, pkg):
        """<package>

        Looks up <package> in the Arch Linux AUR."""
        pkg = pkg.lower()
        baseurl = 'https://aur.archlinux.org/rpc.php?type=search&'
        url = baseurl + urlencode({'arg': pkg})
        self.log.debug("PkgInfo: using url %s for 'archaur' command", url)
        fd = utils.web.getUrl(url)
        data = json.loads(fd.decode("utf-8"))
        if data["type"] == "error":
            irc.error(data["results"], Raise=True)
        count = data["resultcount"]
        if count:
            # We want this to be limited to prevent overflow warnings
            # in the bot.
            if count > 150:
                count = '150+'
            s = format("Found %n: ", (data["resultcount"], 'result'))
            for x in data['results'][:150]:
                verboseInfo = ''
                if self.registryValue("verbose"):
                    verboseInfo = format("[ID: %s Votes: %s]", x['ID'],
                                         x['NumVotes'])
                s += "{name} - {desc} \x02({version} {verbose})\x02, " \
                    .format(name=x['Name'], desc=x['Description'],
                            version=x['Version'], verbose=verboseInfo)
            friendly_url = 'https://aur.archlinux.org/packages/?' + \
                urlencode({'K': pkg})
            irc.reply(s + format('View more at: %u', friendly_url))
        else:
            irc.error("No results found.", Raise=True)
    archaur = wrap(archaur, ['somethingWithoutSpaces'])

    def pkgsearch(self, irc, msg, args, distro, query):
        """<distro> <query>

        Looks up <query> in <distro>'s website. Valid <distro>'s include
        'debian', 'ubuntu', and 'debian-archive'."""
        distro = distro.lower()
        if distro not in addrs.keys():
            distro = _getDistro(distro)
        try:
            url = '%ssearch?keywords=%s' % (addrs[distro], quote(query))
        except KeyError:
            irc.error(unknowndist, Raise=True)
        try:
            fd = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)
        soup = BeautifulSoup(fd)
        # Debian/Ubuntu use h3 for result names in the format 'Package abcd'
        results = [pkg.string.split()[1] for pkg in soup.find_all('h3')]
        if results:
            s = format("Found %n: \x02%L\x02, View more at: %u",
                       (len(results), 'result'), results, url)
            irc.reply(s)
        else:
            e = "No results found."
            try:
                # Look for "too many results" errors and others reported by the
                # web interface.
                if distro == "debian":
                    errorParse = soup.find("div", class_="note").p
                else:
                    errorParse = soup.find("p", attrs={"id":
                                                       "psearchtoomanyhits"})
                if errorParse:
                    for br in errorParse.findAll('br'):
                        br.replace_with(" ")
                    e = errorParse.text.strip()
            except AttributeError:
                pass
            irc.error(e)
    pkgsearch = wrap(pkgsearch, ['somethingWithoutSpaces',
                                 'somethingWithoutSpaces'])

    @wrap(['somethingWithoutSpaces', 'somethingWithoutSpaces'])
    def filesearch(self, irc, msg, args, release, query):
        """<release> <file query>

        Searches what package in Debian or Ubuntu has which file. <release> is the
        codename/release name (e.g. xenial or jessie)."""
        release = release.lower()
        distro = _getDistro(release)

        try:
            url = '%ssearch?keywords=%s&searchon=contents&suite=%s' % (addrs[distro], quote(query), quote(release))
        except KeyError:
            irc.error(unknowndist, Raise=True)

        try:
            fd = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)

        soup = BeautifulSoup(fd)

        results = []
        # Get results from table entries, minus the first one which is used for headings.
        contentdiv = soup.find('div', attrs={'id': "pcontentsres"})
        if contentdiv:
            for tr in contentdiv.find_all("tr")[1:]:
                tds = tr.find_all('td')
                try:
                    filename, packages = map(_normalize, [tds[0].get_text(), tds[1].get_text()])
                except IndexError:
                    continue
                results.append('%s: %s' % (ircutils.bold(filename), packages))

        if results:
            irc.reply('; '.join(results))
        else:
            try:
                e = _normalize(soup.find("div", class_="perror").get_text())
            except AttributeError:
                e = "No results found."
            irc.error(e)

    @wrap(['somethingWithoutSpaces',
           'somethingWithoutSpaces',
           getopts({'exact': ''})])
    def linuxmint(self, irc, msg, args, release, query, opts):
        """<release> <package> [--exact]

        Looks up <package> in Linux Mint's repositories. If --exact is given,
        look up packages by the exact package name. Otherwise, look it up
        as a simple glob pattern."""

        addr = 'http://packages.linuxmint.com/list.php?release=' + \
            quote(release)

        try:
            fd = utils.web.getUrl(addr).decode("utf-8")
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)

        soup = BeautifulSoup(fd)
        # Linux Mint puts their package lists in tables
        results = soup.find_all("td")

        packages = []
        query = query.lower()
        exact = 'exact' in dict(opts)

        for result in results:
            name = result.contents[0].string  # Package name

            if query == name or (query in name and not exact):
                # This feels like really messy code, but we have to find tags
                # relative to our results.
                # Ascend to find the section name (in <h2>):
                section = result.parent.parent.parent.previous_sibling.\
                    previous_sibling.string

                # Find the package version in the next <td>; for some reason we
                # have to go two siblings further, as the first .next_sibling
                # returns '\n'. This is mentioned briefly in Beautiful Soup 4's
                # documentation...
                version = result.next_sibling.next_sibling.string

                # We format our found dictionary this way because the same
                # package can exist multiple times in different sections of
                # the repository (e.g. one in Main, one in Backports, etc.)
                packages.append('%s \x02(%s)\x02 [\x02%s\x02]' % (name, version, section))

        if packages:  # If we have results
            s = format('Found %n: %L, %s %u', (len(packages), 'result'), packages,
                       _('View more at: '), addr)
            irc.reply(s)
        else:
            irc.error('No results found.')


    @wrap([getopts({'release': 'somethingWithoutSpaces'}), additional('somethingWithoutSpaces')])
    def fedora(self, irc, msg, args, opts, query):
        """[--release <release>] [<package name>]

        Looks up <package> in Fedora's repositories. Globs (*, ?) are supported here. <release> is
        the release version: e.g. 'f25' or 'master' (for rawhide). If no package is given, a list
        of available releases will be shown."""
        opts = dict(opts)
        if query is None:
            # No package given; show available releases.
            url = 'https://admin.fedoraproject.org/pkgdb/api/collections?format=json'
        else:
            url = 'https://admin.fedoraproject.org/pkgdb/api/packages/%s?format=json' % quote(query)
            if 'release' in opts:
                url += '&branches=%s' % quote(opts['release'])

        self.log.debug("PkgInfo: using url %s for 'fedora' command", url)
        try:
            fd = utils.web.getUrl(url).decode("utf-8")
        except utils.web.Error as e:
            if '404' in str(e):
                e = 'No results found.'
                if '*' not in query:
                    e += " Try wrapping your query with *'s: '*%s*'" % query
            irc.error(e, Raise=True)
        data = json.loads(fd)

        if query is None:
            data = data['collections']
            collections = ['%s (%s %s, %s)' % (ircutils.bold(c['branchname']), c['name'], c['version'], c['status']) for c in data]
            s = format('Available releases to look up: %L', sorted(collections))
        else:
            def formatdesc(s):
                # Fedora's package descriptions have newlines inserted in them at strange positions,
                # sometimes even inside sentences. We'll break at the first sentence here:
                s = s.split('.')[0].strip()
                s = re.sub('\n+', ' ', s)
                return s

            results = ['%s: %s' % (ircutils.bold(pkg['name']), formatdesc(pkg['description']))
                       for pkg in data["packages"]]
            friendly_url = 'https://apps.fedoraproject.org/packages/s/%s' % query
            s = format('Found %n: %s; View more at %u', (len(results), 'result'), '; '.join(results),
                       friendly_url)
        irc.reply(s)

    @wrap(['positiveInt', additional('somethingWithoutSpaces'), additional('somethingWithoutSpaces'),
           getopts({'arch': 'somethingWithoutSpaces', 'exact': '', 'startswith': ''})])
    def centos(self, irc, msg, args, release, repo, query, opts):
        """<release> [<repository> <package name>] [--arch <arch>] [--startswith|--exact]

        Looks up <package> in CentOS's repositories. <release> is the release
        version (6, 7, etc.), and <repository> is the repository name.
        You can find a list of possible repository names here:
        http://mirror.centos.org/centos/7/ (each folder is a repository).

        Supported values for <arch> include x86_64 and i386 (prior to CentOS 7),
        and defaults to x86_64.

        If <repository> is not given, a list of available ones will be shown instead.

        If --startswith is given, results starting with the given query are shown. If --exact
        is given, only exact matches are shown."""

        # TL;DR CentOS doesn't have a package lookup interface, but only an autoindexed
        # file server... We must find all repositories, package URLs, etc. that way.
        opts = dict(opts)
        exact = opts.get('exact')
        startswith = opts.get('startswith')
        arch = opts.get('arch') or 'x86_64'

        url = 'http://mirror.centos.org/centos/%s' % release
        if repo:
            if query:
                query = query.lower()
                # Both repo and package name were given, so look in folders there.
                # Note: different CentOS versions different paths for their pool, ugh.
                for folder in ('Packages', 'RPMS', 'openstack-juno', 'openstack-kilo',
                        'CentOS'):
                    url = 'http://mirror.centos.org/centos/%s/%s/%s/%s/' % \
                        (release, repo, arch, folder)
                    self.log.debug("PkgInfo: trying url %s for 'centos' command", url)
                    try:
                        fd = utils.web.getUrl(url).decode("utf-8")
                    except utils.web.Error:
                        continue
                    else:
                        break
                else:
                    irc.error('Unknown repository %r.' % repo, Raise=True)
            else:
                # Giving a repository but no package name is useless. Usually there
                # are too many results to display without filtering anyways.
                irc.error("Missing package query.", Raise=True)
        else:  # No repository given; list the ones available.
            fd = utils.web.getUrl(url).decode("utf-8")

        soup = BeautifulSoup(fd)
        # The first two tables are for the navigation bar; the third is the actual autoindex
        # content.
        res = []
        packagetable = soup.find_all('table')[2]

        for tr in packagetable.find_all('tr')[3:]:
            try:
                entry = tr.find_all('td')[1].a.text
            except IndexError:
                continue

            entry = entry.lower()
            if not query:  # No query filter given; show everything.
                res.append(entry)
            elif exact:
                if query == entry:  # Exact match
                    res.append(entry)
                    continue
            elif startswith:
                if entry.startswith(query):  # startswith() match
                    res.append(entry)
                    continue
            elif query in entry:  # Default substring search
                res.append(entry)
                continue

        if res:
            irc.reply(format('Found %n: %L; View more at: %u', (len(res), 'result'), res, url))
        else:
            irc.error('No results found.')

    @wrap(['something', getopts({'exact': ''})])
    def freebsd(self, irc, msg, args, search, optlist):
        """<query> [--exact]

        Searches for <query> in FreeBSD's Ports database (case sensitive).
        If --exact is given, only exact port name matches will be shown."""
        search
        url = 'https://www.freebsd.org/cgi/ports.cgi?' + urlencode({'query': search})
        data = utils.web.getUrl(url)
        soup = BeautifulSoup(data)
        res = {}
        exact = 'exact' in dict(optlist)
        for dt in soup.find_all('dt'):
            pkgname = dt.text
            if exact and pkgname.rsplit('-', 1)[0] != search:
                continue
            # In this case, we only want the first line of the description, in order
            # to keep things short.
            desc = dt.next_sibling.next_sibling.text.split('\n')[0]
            res[pkgname] = desc
        if res:
            # Output results in the form "pkg1: description; pkg2: description; ..."
            s = ["%s: %s" % (ircutils.bold(pkg), desc) for pkg, desc in res.items()]
            s = format('Found %n: %s; View more at %u', (len(res), 'result'), '; '.join(s), url)
            irc.reply(s)
        else:
            irc.error('No results found.')

Class = PkgInfo

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
