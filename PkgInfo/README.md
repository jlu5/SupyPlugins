Fetches package information from the repositories of Debian, Arch Linux, Linux Mint, and Ubuntu.

This plugin uses the following APIs:
- For Debian and Ubuntu, Debian's [madison.php](//qa.debian.org/madison.php) (used by the `vlist` command)
- For Arch Linux and its AUR, [AurJson](//wiki.archlinux.org/index.php/AurJson) and the [Arch Linux Web Interface](//wiki.archlinux.org/index.php/Official_Repositories_Web_Interface)

Everything else is parsed as HTML using the Beautiful Soup 4 library.

### Searching Debian/Ubuntu packages

#### Package details

```
<GLolol> pkg sid bash
<Atlas> Package: bash (4.3-11) in sid - GNU Bourne Again SHell, View more at: <https://packages.debian.org/sid/bash>
```

#### Package details (source)

```
<GLolol> `pkg sid bash --source
<Atlas> Package: bash (4.3-12) in sid - Built packages: bash, bash-builtins, bash-doc, and bash-static, View more at: <https://packages.debian.org/source/sid/bash>
```
#### Viewing (build-)dependencies

```
<GLolol> `pkg sid bash --source --depends
<Atlas> Package bash dependencies: adep: autoconf, adep: autotools-dev, adep: bison, adep: libncurses5-dev, adep: texinfo, adep: texi2html, adep: debhelper (>= 5), adep: locales, adep: gettext, adep: sharutils, adep: time, adep: xz-utils, adep: dpkg-dev (>= 1.16.1), idep: texlive-latex-base, idep: ghostscript, idep: (1 more message)

<GLolol> `pkg sid bash --depends
<Atlas> Package bash dependencies: dep: dash (>= 0.5.5.1-2.2), dep: libc0.1 (>= 2.17-91) [kfreebsd-amd64, kfreebsd-i386], dep: libc0.3 (>= 2.15) [hurd-i386], dep: libc6 (>= 2.15) [not alpha, arm64, hurd-i386, kfreebsd-amd64, kfreebsd-i386, mips, mipsel, ppc64el, sh4, x32], dep: libc6 (>= 2.16) [x32], dep: libc6 (>= 2.17) [arm64, ppc64el], dep: libc6 (>= 2.19) [mips, (1 more message)
```

#### Version listing

(`vlist --reverse` lists packages newest to oldest)

```
<GLolol> vlist ubuntu firefox --reverse
<Atlas> Found 35 results: vivid (34.0+build2-0ubuntu2 [source, amd64, i386]), utopic (33.0+build2-0ubuntu0.14.10.1 [source, amd64, i386]), trusty-updates (33.0+build2-0ubuntu0.14.04.1 [source, amd64, i386]), trusty-security (33.0+build2-0ubuntu0.14.04.1 [source, amd64, i386]), precise-updates (33.0+build2-0ubuntu0.12.04.1 [source, amd64, i386]), precise-security (33.0+build2-0ubuntu0.12.04.1 [source, amd64, (5 more messages)
```

#### Generic package lookup

```
<GLolol> pkgsearch debian perl
<Atlas> Found 23 results: perl, perl-base, perl-byacc, perl-cross-debian, perl-debug, perl-depends, perl-doc, perl-doc-html, perl-mapscript, perl-modules, perl-suid, perl-tk, perlbal, perlbrew, perlconsole, perlindex, perlmagick, perlpanel, perlprimer, perlprimer-doc, perlrdf, perlsgml, and perltidy, View more at: <https://packages.debian.org/search?keywords=perl>
```

### Arch Linux packages

```
<GLolol> archpkg bash
<Atlas> Found 8 results: bash-docs - Advanced Bash-Scripting Guide in HTML (10) [any], bash-completion - Programmable completion for the bash shell (2.1) [any], bashdb - A debugger for Bash scripts loosely modeled on the gdb command syntax (4.3_0.9) [any], screenfetch - CLI Bash script to show system/theme info in screenshots (3.6.5) [any], bash - The GNU Bourne Again shell (4.3.030) [i686, x86_64], (1 more message)
```

#### Arch Linux AUR

```
<GLolol> archaur bash
<Atlas> Found 150+ results: dvdwizard - A set of bash scripts for converting MPEG streams into DVDs with chapters and menus (0.7.1-1 [ID:1166 Votes:26]), bash-completion-xmms2 - bash-completion for xmms2 (20051023-2 [ID:6033 Votes:11]), imageshack-upload - Bash script for uploading images to imageshack.us (0.4-3 [ID:7478 Votes:44]), tuxrip - Bash script for ripping and encoding DVD titles in mpeg4 format (39 more messages)
```

### Linux Mint packages

```
<GLolol> mintpkg Rebecca nemo
<Atlas> Found 22 results: gir1.2-nemo-3.0 [Main] (2.4.4+rebecca), libnemo-extension-dev [Main] (2.4.4+rebecca), libnemo-extension1 [Main] (2.4.4+rebecca), nemo [Main] (2.4.4+rebecca), nemo-compare [Main] (2.4.0+rebecca), nemo-data [Main] (2.4.4+rebecca), nemo-dbg [Main] (2.4.4+rebecca), nemo-dropbox [Main] (2.4.0+rebecca), nemo-emblems [Main] (2.4.3+rebecca), nemo-filename-repairer (2 more messages)
```
