Fetches package information from the repositories of various \*nix distributions. Currently it supports:
- Arch Linux
- CentOS (via a separate `centos` command)
- Debian
- Fedora
- FreeBSD
- Gentoo
- Linux Mint
- Ubuntu

This plugin requires the [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) Python module.

### Package information

**Synopsis**: `pkg <distro/release name> <package name> [--depends] [--source]`

The `pkg` command fetches package information from distribution sources, with additional support for showing source package info (via `--source`) and dependencies (`--depends`) for some OSes.

This command supports:
- Arch Linux (distro names `arch`/`archlinux` and `aur`/`archaur`)
- Debian (using release codenames such as `sid`, `unstable`, `stretch`, `stable`)
- FreeBSD (distro name `freebsd`)
- Fedora (distro name `fedora`)
- Gentoo (distro name `gentoo`)
- Linux Mint (release codenames such as `sonya` or `betsy`)
- Ubuntu (release codenames such as `bionic` or `xenial`).

This command replaces the `archlinux`, `archaur`, `freebsd`, and `linuxmint` commands from earlier versions of PkgInfo.

```
<GLolol> `pkg stretch nginx
<Atlas> Package: nginx (1.10.3-1+deb9u1) in stretch - small, powerful, scalable web/proxy server <https://packages.debian.org/stretch/nginx>
<GLolol> `pkg stretch bash --source
<Atlas> Package: bash (4.4-5) in stretch - Built packages: bash, bash-builtins, bash-doc, and bash-static <https://packages.debian.org/source/stretch/bash>

<GLolol> `pkg arch chromium
<Atlas> Package: chromium (66.0.3359.139) in extra - A web browser built for speed, simplicity, and security <https://www.archlinux.org/packages/extra/x86_64/chromium>
<GLolol> `pkg archaur chromium-beta
<Atlas> Package: chromium-beta (64.0.3282.99-1) in Arch Linux AUR - A web browser built for speed, simplicity, and security (beta channel) [Popularity: 0; Votes: 0] <https://aur.archlinux.org/packages/chromium-beta/>

<GLolol> `pkg freebsd python36
<Atlas> Package: python36 (3.6.5) in FreeBSD Ports - Interpreted object-oriented programming language <https://www.freebsd.org/cgi/ports.cgi?stype=name&query=python36>

<GLolol> `pkg fedora gnome-shell
<Atlas> Package: gnome-shell (3.29.1) in Fedora - no description available <https://apps.fedoraproject.org/packages/gnome-shell>
```

#### Viewing (build-)dependencies

--depends is only supported for Arch Linux, Arch AUR, Debian, FreeBSD, and Ubuntu.

```
<GLolol> `pkg sid bash --source --depends
<Atlas> Package bash dependencies: adep: autoconf, adep: autotools-dev, adep: bison, adep: libncurses5-dev, adep: texinfo, adep: texi2html, adep: debhelper (>= 5), adep: locales, adep: gettext, adep: sharutils, adep: time, adep: xz-utils, adep: dpkg-dev (>= 1.16.1), idep: texlive-latex-base, idep: ghostscript, idep: (1 more message)

<GLolol> `pkg freebsd screen --depends
<Atlas> screen requires: gettext-runtime-0.19.8.1_1, gmake-4.2.1_2, indexinfo-0.3.1
```

### Package search

**Synopsis:** `pkgsearch <distro> <search query>`

The `pkgsearch` command provides package searches on various distros. This supports all distros that `pkg` does except for Fedora.

```
<GLolol> `pkgsearch arch firefox
<Atlas> Found 207 results: arch-firefox-search, bluegriffon, firefox, firefox-adblock-plus, firefox-developer-edition, firefox-developer-edition-i18n-ach, firefox-developer-edition-i18n-af, firefox-developer-edition-i18n-an, firefox-developer-edition-i18n-ar, firefox-developer-edition-i18n-as, firefox-developer-edition-i18n-ast, firefox-developer-edition-i18n-az, firefox-developer- (14 more messages)

<GLolol> `pkgsearch debian geany-plugin
<Atlas> Found 86 results: geany-plugin-addons, geany-plugin-addons-dbgsym, geany-plugin-autoclose, geany-plugin-autoclose-dbgsym, geany-plugin-automark, geany-plugin-automark-dbgsym, geany-plugin-codenav, geany-plugin-codenav-dbgsym, geany-plugin-commander, geany-plugin-commander-dbgsym, geany-plugin-ctags, geany-plugin-ctags-dbgsym, geany-plugin-debugger, geany-plugin-defineformat,  (6 more messages)

<GLolol> `pkgsearch ubuntu unity-scope
<Atlas> Found 54 results: libunity-scopes-cli, libunity-scopes-dev, libunity-scopes-doc, libunity-scopes-json-def-desktop, libunity-scopes-json-def-phone, libunity-scopes-qt-dev, libunity-scopes-qt-doc, libunity-scopes-qt0.2, libunity-scopes1, libunity-scopes1.0, unity-scope-audacious, unity-scope-calculator, unity-scope-chromiumbookmarks, unity-scope-clementine, unity-scope-click,  (3 more messages)
```

### Version listing (Debian and Ubuntu)

**Synopsis:**: `vlist <distribution> <package name> [--reverse]`

```
<GLolol> `vlist debian variety
<Atlas> Found 4 results: jessie-backports (0.6.3-5~bpo8+1 [source, all]), stretch (0.6.3-5 [source, all]), buster (0.6.7-1 [source, all]), and sid (0.6.7-1 [source, all]); View more at: <https://packages.debian.org/search?keywords=variety>

<GLolol> `vlist ubuntu libreoffice --reverse
<atlas> Found 55 results: cosmic/universe (1:6.0.3-0ubuntu1 [amd64, i386]), cosmic (1:6.0.3-0ubuntu1 [source]), bionic/universe (1:6.0.3-0ubuntu1 [amd64, i386]), bionic (1:6.0.3-0ubuntu1 [source]), artful-updates/universe (1:5.4.6-0ubuntu0.17.10.1 [amd64, i386]), artful-updates (1:5.4.6-0ubuntu0.17.10.1 [source]), artful-security/universe (1:5.4.5-0ubuntu0.17.10.5 [amd64, i386]), artful-security  (7 more messages)
```

### CentOS packages

**Synopsis**: `centos <release> [<repository> <package name>] [--arch <arch>] [--startswith|--exact]`

This lookup command is provided as a separate command due to very limited searching abilities through the CentOS website.

```
<GLolol> `centos 7 os zsh
<Atlas> Available RPMs: zsh-5.0.2-7.el7.x86_64.rpm and zsh-html-5.0.2-7.el7.x86_64.rpm
<GLolol> `centos 7 os python
<Atlas> Available RPMs: MySQL-python-1.2.3-11.el7.x86_64.rpm, OpenIPMI-python-2.0.19-11.el7.x86_64.rpm, abrt-addon-python-2.1.11-19.el7.centos.0.3.x86_64.rpm, abrt-python-2.1.11-19.el7.centos.0.3.x86_64.rpm, abrt-python-doc-2.1.11-19.el7.centos.0.3.noarch.rpm, antlr-python-2.7.7-30.el7.noarch.rpm, at-spi-python-1.32.0-12.el7.x86_64.rpm, audit-libs-python-2.4.1-5.el7.x86_64.rpm, (25 more messages)
```

## Implementation Details

This plugin uses the following APIs:
- For Debian and Ubuntu, Debian's [madison.php](//qa.debian.org/madison.php) (used by the `vlist` command)
- For Arch Linux and its AUR, [AurJson](//wiki.archlinux.org/index.php/AurJson) and the [Arch Linux Web Interface](//wiki.archlinux.org/index.php/Official_Repositories_Web_Interface)
- For Fedora, the Product Definition Center API: https://pdc.fedoraproject.org/

Everything else is parsed as HTML using the Beautiful Soup 4 library.
