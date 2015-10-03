# SupyPlugins
[![Build Status](https://travis-ci.org/GLolol/SupyPlugins.svg?branch=master)](https://travis-ci.org/GLolol/SupyPlugins)

My collection of plugins for [Limnoria](https://github.com/ProgVal/Limnoria). This repository is provided **AS IS**, **without any warranty**! It may glitch, break, or spontaneously combust at any time. You have been warned!

## Installation
The recommended way of fetching plugins in this repository is to clone the git repository:

* `$ git clone https://github.com/GLolol/SupyPlugins`

and adding the folder to your bot's `config directories.plugins`.

**You will need a working copy of [Limnoria](https://github.com/ProgVal/Limnoria) running on Python 2.7 or Python 3.4+.** Anything older will *not* work.

If you are using a recent version of Limnoria's PluginDownloader, you can also fetch [individual plugins](#list-of-plugins) by running:

* `install GLolol <plugin>`

on your bot.

## Support
If you have any questions, concerns, or feature requests, please feel free to submit an issue. Pull requests are welcome.

Or, you can find me on IRC at: `irc.overdrive.pw #dev` ([webchat](http://webchat.overdrive.pw/?channels=dev))

## License
Unless otherwise noted, all plugins are available under a 3 clause BSD license (inserted at the top of each file).

## List of plugins
Please note that this list may not always be up to date; your best bet is to actually browse the code for yourself! Any specific plugin dependencies should also be listed.

Most of these plugins also have their own READMEs in their folders; you can usually find a usage demonstration or further explanation of what they do.

##### BonusLevel
- Snarfer for various things on [BonusLevel.org](http://www.bonuslevel.org/).
    - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

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
- LastFM plugin, forked from [krf/supybot-lastfm](https://github.com/krf/supybot-lastfm). Also available as a [separate repository](https://github.com/GLolol/supybot-lastfm).

##### [NoTrigger](NoTrigger/README.md)
- Anti-abuse script; prevents the bot from triggering other bots by modifying its output slightly. For more information, see [NoTrigger/README.md](NoTrigger/README.md).

##### [Namegen](Namegen/README.md)
- A small random name generator.

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

##### [RelayNext](RelayNext/README.md)
- Next generation relayer plugin, designed with two-way relays in mind.

##### Replacer
- History replacer using sed-style expressions.

##### SupyMisc
- Some assorted commands that don't seem to fit anywhere else.

##### SysDNS
- An alternative to Supybot's built-in DNS function, using the `host` DNS lookup utility on the host machine.
    * **Requires:** `host` DNS lookup binary (as in `/usr/bin/host`)

##### Voteserv
- A plugin for storing and manipulating votes/polls.

##### [Weather](Weather/README.md)
- My fork of [reticulatingspline's Weather](https://github.com/reticulatingspline/Weather) plugin. [Source](https://github.com/GLolol/Supybot-Weather)

##### Wikifetch
- Fork of [ProgVal's Wikipedia plugin](https://github.com/ProgVal/Supybot-plugins), with support for other wikis (via a `--site` option) and other improvements.

##### [WTE](WTE/README.md)
- Worst Translations Ever! plugin. Translates text through multiple rounds of Google Translate to get some interesting results!
   - **Note: This plugin requires Python 3!**
