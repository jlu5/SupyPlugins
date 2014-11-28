Fetches package information from the repositories of Debian, Arch Linux, Linux Mint, and Ubuntu.

This plugin uses the following APIs:
- For Debian and Ubuntu, Debian's [madison.php](//qa.debian.org/madison.php) (used for the 'vlist' command)
- For Arch Linux and its AUR, [AurJson](//wiki.archlinux.org/index.php/AurJson) and the [Arch Linux Web Interface](//wiki.archlinux.org/index.php/Official_Repositories_Web_Interface)

Everything else is parsed as HTML using the Beautiful Soup 4 library.

### Usage

#### Searching for Debian/Ubuntu packages:

(`vlist --reverse` lists packages newest to oldest)

```
<GLolol> pkg sid bash
<Atlas> Package: bash (4.3-11) in sid - GNU Bourne Again SHell, View more at: <https://packages.debian.org/sid/bash>
<GLolol> vlist ubuntu firefox --reverse
<Atlas> Found 35 results: vivid (34.0+build2-0ubuntu2 [source, amd64, i386]), utopic (33.0+build2-0ubuntu0.14.10.1 [source, amd64, i386]), trusty-updates (33.0+build2-0ubuntu0.14.04.1 [source, amd64, i386]), trusty-security (33.0+build2-0ubuntu0.14.04.1 [source, amd64, i386]), precise-updates (33.0+build2-0ubuntu0.12.04.1 [source, amd64, i386]), precise-security (33.0+build2-0ubuntu0.12.04.1 [source, amd64, (5 more messages)
<GLolol> pkgsearch debian perl
<Atlas> Found 23 results: perl, perl-base, perl-byacc, perl-cross-debian, perl-debug, perl-depends, perl-doc, perl-doc-html, perl-mapscript, perl-modules, perl-suid, perl-tk, perlbal, perlbrew, perlconsole, perlindex, perlmagick, perlpanel, perlprimer, perlprimer-doc, perlrdf, perlsgml, and perltidy, View more at: <https://packages.debian.org/search?keywords=perl>

```

#### Arch Linux packages:

```
<GLolol> archpkg bash
<Atlas> Found 8 results: bash-docs - Advanced Bash-Scripting Guide in HTML (10) [any], bash-completion - Programmable completion for the bash shell (2.1) [any], bashdb - A debugger for Bash scripts loosely modeled on the gdb command syntax (4.3_0.9) [any], screenfetch - CLI Bash script to show system/theme info in screenshots (3.6.5) [any], bash - The GNU Bourne Again shell (4.3.030) [i686, x86_64], (1 more message)
<GLolol> archaur bash
<Atlas> Found 150+ results: dvdwizard - A set of bash scripts for converting MPEG streams into DVDs with chapters and menus (0.7.1-1 [ID:1166 Votes:26]), bash-completion-xmms2 - bash-completion for xmms2 (20051023-2 [ID:6033 Votes:11]), imageshack-upload - Bash script for uploading images to imageshack.us (0.4-3 [ID:7478 Votes:44]), tuxrip - Bash script for ripping and encoding DVD titles in mpeg4 format (39 more messages)
```

#### Linux Mint packages:

```
<GLolol> mintpkg Rebecca nemo
<Atlas> Found 22 results: gir1.2-nemo-3.0 [Main] (2.4.4+rebecca), libnemo-extension-dev [Main] (2.4.4+rebecca), libnemo-extension1 [Main] (2.4.4+rebecca), nemo [Main] (2.4.4+rebecca), nemo-compare [Main] (2.4.0+rebecca), nemo-data [Main] (2.4.4+rebecca), nemo-dbg [Main] (2.4.4+rebecca), nemo-dropbox [Main] (2.4.0+rebecca), nemo-emblems [Main] (2.4.3+rebecca), nemo-filename-repairer (2 more messages)
```
