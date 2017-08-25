# SupyPlugins

[webchatlink]: https://webchat.overdrivenetworks.com/?channels=dev

[![Travis-CI Build Status](https://travis-ci.org/GLolol/SupyPlugins.svg?branch=master)](https://travis-ci.org/GLolol/SupyPlugins)
![Supported Python versions](https://img.shields.io/badge/python-2.7-blue.svg)
[![Live chat](https://img.shields.io/badge/IRC-live%20chat%20%C2%BB-green.svg)][webchatlink]

My collection of plugins for [Limnoria](https://github.com/ProgVal/Limnoria). This repository is provided **AS IS**, **without any warranty**! It may glitch, break, or spontaneously combust at any time. You have been warned!

**This branch contains the legacy Python 2 branch for SupyPlugins, which will only receive maintenance updates.** Those wanting new features and plugins should migrate their bot to Python 3 and use the *master* branch, as Python 2 is EOL in 2020.

## Installation
The recommended way of fetching plugins in this repository is to clone the git repository:

* `$ git clone https://github.com/GLolol/SupyPlugins`

and add the folder to your bot's `config directories.plugins`.

**You will need a working copy of [Limnoria](https://github.com/ProgVal/Limnoria) running on Python 2.7 or Python 3.4+.** Anything older will *not* work.

If you are using a recent version of Limnoria's PluginDownloader, you can also fetch [individual plugins](#list-of-plugins) by running:

* `install GLolol <plugin>`

on your bot.

## Support
If you have any questions, concerns, or feature requests, please feel free to submit an issue. Pull requests are welcome.

Or, you can find me on IRC at: `irc.overdrivenetworks.com #dev` ([webchat][webchatlink])

## License
Unless otherwise noted, all plugins are available under a 3 clause BSD license (inserted at the top of each file).

## List of plugins
Please note that this list may not always be up to date; your best bet is to actually browse the code for yourself! Any specific plugin dependencies should also be listed.

Most of these plugins also have their own READMEs in their folders; you can usually find a usage demonstration or further explanation of what they do.

##### CtcpNext
- Alternative to the official Ctcp plugin, with a database for configurable replies.

##### DDG
- Provides an interface to DuckDuckGo's web search.
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### FML
- Displays random entries from fmylife.com.

##### Isup
- Provides a simple command to check whether a website is up or down (using [isup.me](http://isup.me)).

##### LastFM
- LastFM plugin, forked from [krf/supybot-lastfm](https://github.com/krf/supybot-lastfm).

##### [Namegen](Namegen/README.md)
- A small random name generator.

##### [NoTrigger](NoTrigger/README.md)
- Anti-abuse script; prevents the bot from triggering other bots by modifying its output slightly. For more information, see [NoTrigger/README.md](NoTrigger/README.md).

##### [OperUp](OperUp/README.md)
- Allows Supybot to oper up on configured networks, automatically (on connect) and on demand.

##### PassGen
- Generates random passwords on the fly!

##### [PkgInfo](PkgInfo/README.md)
- Fetches package information from various Linux and BSD distros' software repositories.
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### PortLookup
- Looks up commonly used UDP and TCP port numbers from Wikipedia: https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### QuakeNet
- Log in to Quakenet's Q Service via CHALLENGEAUTH. This plugin was written by request and not officially supported.

##### Restart
- **EXPERIMENTAL**: provides a command to restart Limnoria from IRC.

##### [RelayNext](RelayNext/README.md)
- Next generation relayer plugin, designed with two-way relays in mind.

##### RhymeZone
- Fetches rhymes from http://rhymezone.com/.
    - Unsupported on Python 2 due to string encoding issues.

##### SedRegex
- History replacer using sed-style expressions. Fork of [t3chguy's Replacer plugin](https://github.com/t3chguy/Limnoria-Plugins/tree/master/Replacer).

##### SupyMisc
- Some assorted commands that don't seem to fit anywhere else.

##### SysDNS
- An alternative to Supybot's built-in DNS function, using the `host` DNS lookup utility on the host machine.
    * **Requires:** `host` DNS lookup binary (as in `/usr/bin/host`)

##### [TranslateParty](TranslateParty/README.md)
- Translates text through Google Translate multiple times in order to get amusing results.
   - **Note: This plugin requires Python 3!**

##### Voteserv
- A plugin for storing and manipulating votes/polls.

##### [Weather](Weather/README.md)
- My fork of [reticulatingspline's Weather](https://github.com/reticulatingspline/Weather) plugin, with rewritten output handling, explicit location search, and many other tweaks.

##### Wikifetch
- Fork of [ProgVal's Wikipedia plugin](https://github.com/ProgVal/Supybot-plugins), with support for other wikis (via a `--site` option) and other improvements.
