Fetches package information from the repositories of Debian, Arch Linux, Linux Mint, and Ubuntu.

This plugin uses the following APIs:
- For Debian and Ubuntu, Debian's [madison.php](//qa.debian.org/madison.php) (used for 'vlist' command)
- For Arch Linux and its AUR, [AurJson](//wiki.archlinux.org/index.php/AurJson) and the [Arch Linux Repository Web Interface](//wiki.archlinux.org/index.php/Official_Repositories_Web_Interface)

Everything else is parsed as HTML using the Beautiful Soup 4 library.
