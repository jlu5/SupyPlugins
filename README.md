# SupyPlugins
### GLolol's collection of Supybot plugins
[![Build Status](https://travis-ci.org/GLolol/SupyPlugins.svg?branch=master)](https://travis-ci.org/GLolol/SupyPlugins)

This repository includes forks/mods of existing Supybot plugins and some that I've written myself. All of the code in this repository is considered **experimental** and **not** ready for production use. It may glitch, break, or spontaneously combust at any time. You have been warned!

*Note:* This repository is currently being written for Python 2.7/Python 3.4, and has not been tested for compatibility with other Python versions. Older Python versions are unsupported; use them at your own risk!

## Support
If you have any questions, concerns, or feature requests, please feel free to submit an issue. Pull requests are welcome.

Or, you can find me on IRC at: `irc.overdrive.pw #dev` ([webchat](http://webchat.overdrive.pw/?channels=dev))

## License
Unless otherwise noted, all plugins are available under a 3 clause BSD license (inserted at the top of the file).

## List of plugins
Please note that this list may not always be up to date; your best bet is to actually browse the code for yourself!

Any specific plugin dependencies *should* also be listed.

##### Isup
- Provides a simple command to check whether a website is up or down (using [isup.me](http://isup.me)).

##### NoTrigger
- Anti-abuse script; prevents the bot from triggering other bots by modifying its output slightly. 

##### Namegen
- A simple random name generator.

##### OperUp *(deprecated)*
- Simple plugin that allows Supybot to oper up on configured networks, automatically (on connect) and manually. **This plugin is deprecated and will likely be removed in a future release.**
    - *No longer in active development.*

##### PassGen
- Generates random passwords on the fly!

##### PkgInfo
- Fetches package information from Debian, Ubuntu, Arch Linux, and Linux Mint's repositories.
    * ***Requires:*** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) - install it via `pip install beautifulsoup4` or `apt-get install python-bs4`/`python3-bs4` (Debian/Ubuntu)

##### Randomness
- Random commands for my own personal use; you probably don't need this loaded!

##### RelayLink
- [LinkRelay](https://github.com/ProgVal/Supybot-plugins/tree/master/LinkRelay) forked into a different name. See [RelayLink/README.md](RelayLink/README.md) for more details.
    - **Mainstream development has ceased. Any new changes will only be for maintainence purposes/bugfixes.**

##### SupyMisc
- Some assorted commands that don't seem to fit anywhere else.

##### SysDNS
- An alternative to Supybot's built-in DNS function, using DNS lookup utilities (such as host or dig) available on the host machine.
    * ***Requires:*** a DNS lookup binary such as `host` (as in `/usr/bin/host`, installable in Debian/Ubuntu via `apt-get install bind9-host`)

##### TLDInfo
- Checks if something is a valid TLD using IANA's database (http://www.iana.org/domains/root/db/).
