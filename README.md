# SupyPlugins
[![Build Status](https://travis-ci.org/GLolol/SupyPlugins.svg?branch=master)](https://travis-ci.org/GLolol/SupyPlugins)

My collection of plugins for [Supybot/Limnoria](https://github.com/ProgVal/Limnoria). This repository is provided **AS IS**, **without any warranty provided**! It may glitch, break, or spontaneously combust at any time. You have been warned!


## Installation
The recommended way of fetching plugins in this repository is to clone the git repository: 

* `$ git clone https://github.com/GLolol/SupyPlugins` 

and adding the folder to your bot's `config directories.plugins`. 

**You will need a working copy of [Limnoria](https://github.com/ProgVal/Limnoria) running on Python 2.7 and Python 3.4+.** The repository *may* also work with Python 3.2-3.3 (Debian 7/Ubuntu 12.04/Fedora 19-20), but this is relatively untested (besides [some tests with Travis-CI](https://travis-ci.org/GLolol/SupyPlugins/)) and therefore not officially supported. **Anything older will *not* work.**

For those of you using a recent version of Limnoria's PluginDownloader, you can also fetch [individual plugins](#list-of-plugins) by running: 

* `install GLolol <plugin>`

on your bot.

## Support
If you have any questions, concerns, or feature requests, please feel free to submit an issue. Pull requests are welcome.

Or, you can find me on IRC at: `irc.overdrive.pw #dev` ([webchat](http://webchat.overdrive.pw/?channels=dev))

## License
Unless otherwise noted, all plugins are available under a 3 clause BSD license (inserted at the top of each file).

## List of plugins
Please note that this list may not always be up to date; your best bet is to actually browse the code for yourself! Any specific plugin dependencies should also be listed.

Most of these plugins have their own READMEs in their folders; you can check them for a usage demonstration or further explanation of what they do.

##### Isup
- Provides a simple command to check whether a website is up or down (using [isup.me](http://isup.me)).

##### LastFM
- LastFM plugin, forked from [krf/supybot-lastfm](https://github.com/krf/supybot-lastfm). Also available as a [separate repository](https://github.com/GLolol/supybot-lastfm).
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/), lxml (for XML parsing)

##### [NoTrigger](NoTrigger/README.md)
- Anti-abuse script; prevents the bot from triggering other bots by modifying its output slightly. For more information, see [NoTrigger/README.md](NoTrigger/README.md).

##### [Namegen](Namegen/README.md)
- A small random name generator.

##### OperUp *(deprecated)*
- Simple plugin that allows Supybot to oper up on configured networks, automatically (on connect) and manually.
   - **This plugin is deprecated and will likely be removed in a future release.**

##### PassGen
- Generates random passwords on the fly!

##### [PkgInfo](PkgInfo/README.md)
- Fetches package information from Debian, Ubuntu, Arch Linux, and Linux Mint's repositories.
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) - install it via `pip install beautifulsoup4` or `apt-get install python-bs4`/`python3-bs4` (Debian/Ubuntu)

##### Randomness
- Random commands for my own personal use; you probably don't want this loaded!

##### [RelayLink](RelayLink/README.md)
- [LinkRelay](https://github.com/ProgVal/Supybot-plugins/tree/master/LinkRelay) forked into a different name. See [RelayLink/README.md](RelayLink/README.md) for more details.
   - **Mainstream development has ceased. Any new changes will only be for maintainence purposes or bugfixes.**

##### SupyMisc
- Some assorted commands that don't seem to fit anywhere else.

##### SysDNS
- An alternative to Supybot's built-in DNS function, using the `host` DNS lookup utility on the host machine.
    * **Requires:** `host` DNS lookup binary (as in `/usr/bin/host`, installable in Debian/Ubuntu via `apt-get install bind9-host`)

##### Voteserv
- A plugin for storing and manipulating votes/polls.
