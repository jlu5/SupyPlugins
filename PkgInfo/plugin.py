###
# Copyright (c) 2014-2018, James Lu <james@overdrivenetworks.com>
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
import supybot.conf as conf

from collections import OrderedDict, defaultdict
try:  # Python 3
    from urllib.parse import urlencode, quote
except ImportError:  # Python 2
    from urllib import urlencode, quote
import json
import re
import sys
import time
try:
    from bs4 import BeautifulSoup, element
except ImportError:
    raise ImportError("Beautiful Soup 4 is required for this plugin: get it"
                      " at http://www.crummy.com/software/BeautifulSoup/bs4/"
                      "doc/#installing-beautiful-soup")

# Use __builtins__.any and not the supybot.commands version...
any = __builtins__['any'] if isinstance(__builtins__, dict) else __builtins__.any

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PkgInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

DEBIAN_ADDRS = {'ubuntu': 'https://packages.ubuntu.com/',
                'debian': 'https://packages.debian.org/'
               }
_normalize = lambda text: utils.str.normalizeWhitespace(text).strip()

class UnknownDistributionError(ValueError):
    pass

class AmbiguousDistributionError(UnknownDistributionError):
    pass

class UnsupportedOperationError(NotImplementedError):
    pass

class BadRequestError(ValueError):
    pass

class PkgInfo(callbacks.Plugin):
    """Fetches package information from various OS software repositories.."""
    threaded = True

    _get_dependency_color = utils.str.MultipleReplacer(OrderedDict((
        # Arch
        ('depends', '\x0304depends\x03'),
        ('optdepends', '\x0312optdepends\x03'),
        # FreeBSD
        ('requires', '\x0304requires\x03'),
        # Debian/Ubuntu abbreviations
        ('dep', '\x0304dep\x03'),
        ('rec', '\x0312rec\x03'),
        ('sug', '\x0309sug\x03'),
        ('adep', '\x0305adep\x03'),
        ('idep', '\x0302idep\x03'),
        ('enh', '\x0308enh\x03'),
    )))

    @staticmethod
    def _guess_distro_from_release(release):
        """Guesses the Linux distribution from a release codename."""
        release = release.lower()
        debian = ("oldoldstable", "oldstable", "wheezy", "stable",
                  "jessie", "testing", "sid", "unstable", "stretch", "buster",
                  "experimental", "bullseye", "bookworm")
        ubuntu = ("trusty", "xenial", "artful", "bionic", "cosmic")
        mint = ("betsy", "cindy", "qiana", "rebecca", "rafaela", "rosa",
                "sarah", "serena", "sonya", "sylvia", "tara")

        if release.startswith(debian):
            return "debian"
        elif release.startswith(ubuntu):
            return "ubuntu"
        elif release.startswith(mint):
            return "mint"

    def _get_distro_fetcher(self, dist, multi=False):
        dist = dist.lower()
        guess_dist = self._guess_distro_from_release(dist)

        if dist == 'debian' and not multi:
            raise AmbiguousDistributionError("You must specify a distribution version (e.g. 'stretch' or 'unstable')")
        elif dist == 'ubuntu' and not multi:
            raise AmbiguousDistributionError("You must specify a distribution version (e.g. 'trusty' or 'xenial')")
        elif dist in ('mint', 'linuxmint'):
            raise AmbiguousDistributionError("You must specify a distribution version (e.g. 'sonya' or 'betsy')")
        elif dist == 'master':
            raise AmbiguousDistributionError("'master' is ambiguous: for Fedora rawhide, use the release 'rawhide'")

        elif dist in ('archlinux', 'arch'):
            return self._arch_fetcher
        elif dist in ('archaur', 'aur'):
            return self._arch_aur_fetcher
        elif guess_dist == 'debian' or dist == 'debian':
            return self._debian_fetcher
        elif dist in ('fbsd', 'freebsd'):
            return self._freebsd_fetcher
        elif guess_dist == 'ubuntu' or dist == 'ubuntu':
            return self._ubuntu_fetcher
        elif guess_dist == 'mint':
            return self._mint_fetcher
        elif dist == 'fedora':
            return self._fedora_fetcher
        elif dist == 'gentoo':
            return self._gentoo_fetcher

    def _debian_fetcher(self, release, query, baseurl='https://packages.debian.org/', fetch_source=False, fetch_depends=False, multi=False):
        url = baseurl
        query = query.lower()
        if multi:
            url += 'search?%s' % urlencode({'keywords': query})
        else:
            if fetch_source:  # Source package was requested
                url += 'source/'
            url += "{}/{}".format(release, query)

        text = utils.web.getUrl(url).decode("utf-8")

        # Workaround unescaped << in package versions (e.g. "python (<< 2.8)") not being parsed
        # correctly.
        text = text.replace('<<', '&lt;&lt;')

        soup = BeautifulSoup(text)

        if "Error" in soup.title.string:
            err = soup.find('div', attrs={"id": "content"}).find('p').string
            if "two or more packages specified" in err:
                raise UnknownDistributionError("Unknown distribution/release.")

        # If we're using the --depends or search options, handle that separately.
        if multi:
            # Debian and Ubuntu use h3 for result names in the format 'Package abcd'
            return [pkg.string.split()[1] for pkg in soup.find_all('h3')]
        elif fetch_depends:
            items = soup.find('div', {'id': 'pdeps'}).find_all('dl')
            # Store results by type and name, but in an ordered fashion: show dependencies first,
            # followed by recommends, suggests, and enhances.
            # "adep" and "idep" are arch-dependent and arch-independent build-dependencies
            # respectively.
            res = OrderedDict((deptype, []) for deptype in ('dep:', 'rec:', 'sug:', 'enh:', 'adep:', 'idep:'))

            for item_wrapper in items:
                # Get package name and related versions and architectures:
                # <packagename> (>= 1.0) [arch1, arch2]
                last_deptype = ''
                for count, item in enumerate(item_wrapper.find_all('dt')):
                    # The dependency type is in a <span> element in front of the package name,
                    # which is expressed as a link.
                    deptype = item.span.text if item.find('span') else last_deptype
                    last_deptype = deptype
                    if deptype not in res:
                        continue  # Ignore unsupported fields

                    # Also include any parts directly after the package name (usually a version
                    # restriction).
                    try:
                        name = '%s %s' % (ircutils.bold(item.a.text),
                                item.a.next_sibling.replace('\n', '').strip())
                    except AttributeError:
                        # No package link usually means that the package isn't available
                        name = item.string
                        if name:
                            name = ircutils.bold(name.splitlines()[1].strip())
                    name = utils.str.normalizeWhitespace(name).strip()
                    self.log.debug('PkgInfo.debian_fetcher: got %s %s for package %s', deptype, name, query)

                    if count == 0:
                        res[deptype].append(name)
                    else:
                        # OR dependency; format accordingly
                        res[deptype][-1] += " or %s" % name

            return res

        # Fetch package information from the packages page's <meta> tags.
        desc = soup.find('meta', attrs={"name": "Description"})["content"]
        keywords = soup.find('meta', attrs={"name": "Keywords"})["content"]
        keywords = keywords.replace(",", "").split()
        try:
            real_distribution = keywords[1]
        except IndexError:
            return  # No such package
        version = keywords[-1]

        # Override the description if we selected source lookup, since the meta
        # tag Description will be empty for those. Replace this with a list
        # of binary packages that the source package builds.
        if fetch_source:
            binaries = soup.find('div', {'id': "pbinaries"})
            binaries = [ircutils.bold(obj.a.text) for obj in binaries.find_all('dt')]
            desc = format('Built packages: %L', binaries)

        # Handle virtual packages by showing a list of packages that provide it
        if version == "virtual":
            providing = [ircutils.bold(obj.a.text) for obj in soup.find_all('dt')]
            desc = "Virtual package provided by: %s" % ', '.join(providing[:10])
            if len(providing) > 10:  # XXX: arbitrary limit
                desc += " and %s others" % (ircutils.bold(len(providing) - 10))

        return (query, version, real_distribution, desc, url)

    def _ubuntu_fetcher(self, *args, **kwargs):
        kwargs['baseurl'] = 'https://packages.ubuntu.com/'
        return self._debian_fetcher(*args, **kwargs)

    def _arch_fetcher(self, release, query, fetch_source=False, fetch_depends=False, multi=False):
        search_url = 'https://www.archlinux.org/packages/search/json/?%s&arch=x86_64&arch=any' % \
            urlencode({'q' if multi else 'name': query})

        self.log.debug("PkgInfo: using url %s for arch_fetcher", search_url)

        fd = utils.web.getUrl(search_url)
        data = json.loads(fd.decode("utf-8"))

        if data['valid'] and data['results']:
            if multi:
                return [pkgdata['pkgname'] for pkgdata in data['results']]
            pkgdata = data['results'][0]
            name, version, repo, arch, desc = pkgdata['pkgname'], pkgdata['pkgver'], pkgdata['repo'], pkgdata['arch'], pkgdata['pkgdesc']

            if pkgdata['flag_date']:
                # Mark flagged-as-outdated versions in red.
                version = '\x0304%s\x03' % version

                # Note the flagged date in the package description.
                t = time.strptime(pkgdata['flag_date'], '%Y-%m-%dT%H:%M:%S.%fZ')  # Why can't strptime be smarter and guess this?!
                # Convert the time format to the globally configured one.
                out_t = time.strftime(conf.supybot.reply.format.time(), t)
                desc += ' [flagged as \x0304outdated\x03 on %s]' % out_t

            if fetch_depends:
                deps = set()
                for dep in pkgdata['depends']:
                    # XXX: Arch's API does not differentiate between required deps and optional ones w/o explanation...

                    # Sort through the API info and better explain optional dependencies with reasons in them.
                    if ':' in dep:
                        name, explanation = dep.split(':', 1)
                        dep = '%s (optional; needed for %s)' % (ircutils.bold(name), explanation.strip())
                    else:
                        dep = ircutils.bold(dep)
                    deps.add(dep)

                return {'depends': deps}

            # Package site URLs use a form like https://www.archlinux.org/packages/extra/x86_64/python/
            friendly_url = 'https://www.archlinux.org/packages/%s/%s/%s' % (repo, arch, name)
            return (name, version, repo, desc, friendly_url)
        else:
            return  # No results found!

    def _arch_aur_fetcher(self, release, query, fetch_source=False, fetch_depends=False, multi=False):
        url = 'https://aur.archlinux.org/rpc/?'
        if multi:
            url += urlencode({'arg': query, 'v': 5, 'type': 'search'})
        else:
            url += urlencode({'arg[]': query, 'v': 5, 'type': 'info'})

        self.log.debug("PkgInfo: using url %s for arch_aur_fetcher", url)

        fd = utils.web.getUrl(url)
        data = json.loads(fd.decode("utf-8"))

        if data['results']:
            if multi:
                return [pkgdata['Name'] for pkgdata in data['results']]

            pkgdata = data['results'][0]
            name, version, votecount, popularity, desc = pkgdata['Name'], pkgdata['Version'], \
                pkgdata['NumVotes'], pkgdata['Popularity'], pkgdata['Description']

            verbose_info = ' [Popularity: \x02%s\x02; Votes: \x02%s\x02' % (popularity, votecount)

            if pkgdata['OutOfDate']:
                # Mark flagged-as-outdated versions in red.
                version = '\x0304%s\x03' % version

                flag_time = time.strftime(conf.supybot.reply.format.time(), time.gmtime(pkgdata['OutOfDate']))
                verbose_info += '; flagged as \x0304outdated\x03 on %s' % flag_time
            verbose_info += ']'

            if fetch_depends:
                deplist = pkgdata['MakeDepends'] if fetch_source else pkgdata['Depends']
                deplist = [ircutils.bold(dep) for dep in deplist]

                # Fill in opt depends
                optdepends = set()
                for dep in pkgdata.get('OptDepends', []):
                    if ':' in dep:
                        name, explanation = dep.split(':', 1)
                        dep = '%s (optional; needed for %s)' % (ircutils.bold(name), explanation.strip())
                    else:
                        dep = '%s (optional)' % ircutils.bold(dep)
                    optdepends.add(dep)

                # Note: this is an ordered dict so that depends always show before optdepends
                return OrderedDict((('depends', deplist), ('optdepends', optdepends)))

            # Package site URLs use a form like https://www.archlinux.org/packages/extra/x86_64/python/
            friendly_url = 'https://aur.archlinux.org/packages/%s/' % name
            desc += verbose_info
            return (name, version, 'Arch Linux AUR', desc, friendly_url)
        else:
            if data['type'] == 'error':
                raise BadRequestError(data['error'])

    def _fedora_fetcher(self, release, query, fetch_source=False, fetch_depends=False, multi=False):
        if fetch_source or fetch_depends:
            raise UnsupportedOperationError("--depends and --source lookup are not supported for Fedora")
        elif multi:
            raise UnsupportedOperationError("Package searching is not supported for Fedora")

        friendly_url = 'https://apps.fedoraproject.org/packages/%s' % query

        if not multi:  # The name= arg in the pdc API actually takes a regexp
            query = r'^%s$' % query

        # Sort results by version descendingly
        url = 'https://pdc.fedoraproject.org/rest_api/v1/rpms/?' + urlencode({'name': query, 'ordering': '-version'})

        self.log.debug("PkgInfo: using url %s for fedora_fetcher", url)
        fd = utils.web.getUrl(url).decode("utf-8")
        data = json.loads(fd)

        results = data["results"]

        if not results:
            return  # No results found

        result = results[0]
        return (result['name'], result['version'], 'Fedora', 'no description available', friendly_url)

    def _mint_fetcher(self, release, query, fetch_source=False, fetch_depends=False, multi=False):
        if fetch_depends:
            raise UnsupportedOperationError("--depends lookup is not supported for Linux Mint")

        if fetch_source:
            addr = 'http://packages.linuxmint.com/list-src.php?'
        else:
            addr = 'http://packages.linuxmint.com/list.php?'
        addr += urlencode({'release': release})

        fd = utils.web.getUrl(addr).decode("utf-8")

        soup = BeautifulSoup(fd)

        # Linux Mint puts their package lists in tables, so use HTML parsing
        results = soup.find_all("td")

        versions = {}
        query = query.lower()

        multi_results = []
        for result in results:
            name = result.contents[0].string  # Package name

            if query in name and multi:
                multi_results.append(name)

            elif query == name:
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

                # Create a list of versions because a package can exist multiple
                # times in different sections of the repository (e.g. one in Main,
                # one in Backports, etc.)
                versions[section] = version

        if multi:
            return multi_results
        return (query, ', '.join('%s: %s' % (k, v) for k, v in versions.items()),
                'Linux Mint %s' % release.title(), 'no description available', addr)

    def _freebsd_fetcher(self, release, query, fetch_source=False, fetch_depends=False, multi=False):
        if fetch_source:
            raise UnsupportedOperationError("--source lookup is not supported for FreeBSD")

        url = 'https://www.freebsd.org/cgi/ports.cgi?' + urlencode({'query': query, 'stype': 'name'})
        self.log.debug('PkgInfo: using URL %s for freebsd_fetcher', url)
        data = utils.web.getUrl(url)
        soup = BeautifulSoup(data)

        if multi:
            return [dt.text for dt in soup.find_all('dt')]

        for dt in soup.find_all('dt'):
            pkgname, pkgver = dt.text.rsplit('-', 1)
            self.log.debug('PkgInfo: got pkgname=%s pkgver=%s for freebsd_fetcher', pkgname, pkgver)

            if pkgname == query:
                # In this case, we only want the first line of the description, in order
                # to keep things short.
                info_dd = dt.next_sibling.next_sibling
                desc = info_dd.text.split('\n')[0]

                if fetch_depends:
                    # Depends are displayed as links after an "<i>Requires:</i>" element, which is (supposedly) the
                    # last <i> element per package entry. Iterate over all items following it, filter out
                    # valid <a> tags, and grab+clean up the text from them.
                    return {'requires': [tag.text for tag in info_dd.find_all('i')[-1].next_siblings
                                         if isinstance(tag, element.Tag) and tag.text]}

                return (query, pkgver, 'FreeBSD Ports', desc, url)

    def _gentoo_fetcher(self, _, query, fetch_source=False, fetch_depends=False, multi=False):
        # Gentoo is all sources, so fetch_source is ignored
        if fetch_depends:
            raise UnsupportedOperationError("--depends lookup is not supported for Gentoo")

        url = "https://packages.gentoo.org/packages/"
        query = query.lower()
        if multi:
            url += "search?%s" % urlencode({'q': query})
        else:
            url += query  # Don't encode the / in package name

        text = utils.web.getUrl(url).decode('utf-8')
        soup = BeautifulSoup(text)

        if multi:
            results = [tag.text.strip() for tag in soup.find_all('h3', class_='kk-search-result-header')]
            return results
        else:
            titletag = soup.find(id="package-title")
            name = titletag["data-name"]
            category = titletag["data-category"]
            version = _normalize(soup.find('a', class_="kk-ebuild-link").text)
            desc = _normalize(soup.find('p', class_="kk-package-maindesc").text)

            return (name, version, category, desc, url)

    def _debian_vlist_fetcher(self, pkg, dist, showNewestFirst=True):
        """Parser for the madison API at https://qa.debian.org/madison.php."""
        # This arch value implies 'all' (architecture-independent packages)
        # and 'source' (source packages), in order to prevent misleading
        # "Not found" errors.
        archs = self.registryValue('archs') + ['source', 'all']
        arg = {'package': pkg, 'table': dist, 'a': ','.join(set(archs))}

        url = 'https://qa.debian.org/madison.php?text=on&' + urlencode(arg)
        log.debug("PkgInfo: Using url %s for debian_vlist_fetcher", url)

        d = OrderedDict()
        fd = utils.web.getUrlFd(url)
        for line in fd.readlines():
            L = line.decode("utf-8").split("|")
            name, version, release, archs = map(str.strip, L)
            d[release] = (version, archs)
        if d:
            if showNewestFirst:
                # *sigh*... I wish there was a better way to do this
                d = OrderedDict(reversed(tuple(d.items())))

            if self.registryValue('verbose'):
                items = ["{name} \x02({version} [{archs}])\x02".format(name=k,
                         version=v[0], archs=v[1]) for (k, v) in d.items()]
            else:
                items = ["{name} \x02({version})\x02".format(name=k,
                         version=v[0]) for (k, v) in d.items()]
            s = format('Found %n: %L', (len(d), 'result'), items)
            return s
        else:
            log.debug("PkgInfo: No results found for URL %s", url)

    def package(self, irc, msg, args, dist, query, opts):
        """<distro/release name> <package name> [--depends] [--source]

        Fetches information (version, description, etc.) from various operating system's package repositories.

        If --depends is given, fetches dependency info for the given package instead of general details.
        If --source is given, looks up the package name as a source package instead of a binary package.
        Not all options are supported for all distributions.

        The following OSes are supported:
            Arch Linux (distro name 'arch' or 'archlinux'),
            Arch Linux AUR (distro name 'aur' or 'archaur'),
            Debian (use a release codename such as 'sid', 'unstable', 'stretch', or 'stable'),
            FreeBSD (distro name 'freebsd'),
            Gentoo (distro name 'gentoo'; use category/package-name for package names),
            Linux Mint (use a release codename such as 'sonya' or 'betsy'),
            and
            Ubuntu (use a release codename such as 'trusty' or 'xenial').

        This command replaces the 'archlinux', 'archaur', 'freebsd', and 'linuxmint' commands from earlier versions of PkgInfo."""
        opts = dict(opts)
        fetch_source = 'source' in opts
        fetch_depends = 'depends' in opts
        multi = 'search' in opts

        distro_fetcher = self._get_distro_fetcher(dist, multi=multi)
        if distro_fetcher is None:
            irc.error("Unknown distribution version %r" % dist, Raise=True)

        result = distro_fetcher(dist, query, fetch_source=fetch_source, fetch_depends=fetch_depends, multi=multi)
        if not result:
            if multi:
                irc.error("No results found.", Raise=True)
            else:
                irc.error("Unknown package %r" % query, Raise=True)

        if fetch_depends:
            # results is a dictionary mapping dependency type to a list
            # of packages.
            if not isinstance(result, dict):
                raise UnsupportedOperationError("Internal fetcher error (wrong output type; expected dict but got %s)" % (type(result).__name__))
            if any(result.values()):
                deplists = []
                for deptype, packages in result.items():
                    if packages:
                        deptype = self._get_dependency_color(deptype)
                        if ':' not in deptype:
                            deptype += ':'
                        # Join together the dependency type and package list for each list
                        # that isn't empty.
                        deplists.append("%s %s" % (ircutils.bold(deptype), ', '.join(packages)))
                        log.debug('PkgInfo: joining deplist %r', packages)

                irc.reply(format("%s %s", ircutils.bold(query), '; '.join(deplists)))

            else:
                irc.error("%s doesn't seem to have any dependencies." % ircutils.bold(query))
        else:
            if not isinstance(result, (list, tuple)):
                raise UnsupportedOperationError("Internal fetcher error (wrong output type; expected list or tuple but got %s)" % (type(result).__name__))

            if multi:
                s = format("Found \x02%s\x02 results: %L", len(result), (ircutils.bold(r) for r in result))
                irc.reply(s)
            else:
                # result is formatted in the order: packagename, version, real_distribution, desc, url
                self.log.debug('PkgInfo result args: %s', str(result))
                s = format("Package: \x02%s (%s)\x02 in %s - %s %u", *result)
                irc.reply(s)

    pkg = wrap(package, ['somethingWithoutSpaces', 'somethingWithoutSpaces',
               getopts({'depends': '', 'source': ''})])

    def pkgsearch(self, irc, msg, args, dist, query):
        """<distro> <search query>

        Looks up the search query in the given operating system's package repositories.

        The following OSes are supported:
            Arch Linux (distro name 'arch' or 'archlinux'),
            Arch Linux AUR (distro name 'aur' or 'archaur'),
            Debian (distro name 'debian'),
            FreeBSD (distro name 'freebsd'),
            Gentoo (distro name 'gentoo'),
            Linux Mint (use a release codename such as 'sonya' or 'betsy'),
            and
            Ubuntu (distro name 'ubuntu').

        This command replaces the 'archlinux', 'archaur', 'freebsd', and 'linuxmint' commands from earlier versions of PkgInfo."""

        return self.package(irc, msg, args, dist, query, {'search': True})
    pkgsearch = wrap(pkgsearch, ['somethingWithoutSpaces',
                                 'somethingWithoutSpaces'])

    def vlist(self, irc, msg, args, distro, pkg, opts):
        """<distribution> <package name> [--reverse]

        Fetches all available version of <package name> in <distribution>, if
        such a package exists.

        Supported distributions include 'debian', 'ubuntu', 'derivatives', and 'all'.

        If --reverse is given, show the oldest package versions first."""
        pkg, distro = map(str.lower, (pkg, distro))
        supported = ("debian", "ubuntu", "derivatives", "all")
        if distro not in supported:
            distro = self._guess_distro_from_release(distro)
            if distro is None:
                irc.error("Unknown distribution. This command only supports "
                          "package lookup for Debian and Ubuntu.", Raise=True)

        d = self._debian_vlist_fetcher(pkg, distro, showNewestFirst='reverse' not in dict(opts))
        if not d:
            irc.error("No results found.", Raise=True)
        try:
            url = "{}search?keywords={}".format(DEBIAN_ADDRS[distro], pkg)
            d += format("; View more at: %u", url)
        except KeyError:
            pass

        irc.reply(d)

    vlist = wrap(vlist, ['somethingWithoutSpaces', 'somethingWithoutSpaces',
                 getopts({'reverse': ''})])

    @wrap(['somethingWithoutSpaces', 'somethingWithoutSpaces'])
    def filesearch(self, irc, msg, args, release, query):
        """<release> <file query>

        Searches what package in Debian or Ubuntu has which file.
        <release> is the codename/release name (e.g. xenial or stretch)."""
        release = release.lower()
        distro = self._guess_distro_from_release(release)

        try:
            url = '%ssearch?keywords=%s&searchon=contents&suite=%s' % (DEBIAN_ADDRS[distro], quote(query), quote(release))
        except KeyError:
            irc.error("Unknown distribution. This command only supports "
                      "package lookup for Debian and Ubuntu.", Raise=True)

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
            elif exact:  # Match a package name in the format 'name'-version
                package_pattern = '^{}-[0-9]+'.format(query)
                if re.search(package_pattern, entry):
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

Class = PkgInfo

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
