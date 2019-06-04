# SupyPlugins

[webchatlink]: https://webchat.overdrivenetworks.com/?channels=dev

[![Travis-CI Build Status](https://travis-ci.org/jlu5/SupyPlugins.svg?branch=master)](https://travis-ci.org/jlu5/SupyPlugins)
![Supported Python versions](https://img.shields.io/badge/python-3.4%20and%20later-blue.svg)
[![Live chat](https://img.shields.io/badge/IRC-live%20chat%20%C2%BB-green.svg)][webchatlink]

My collection of plugins for [Limnoria](https://github.com/ProgVal/Limnoria). This repository is provided **AS IS**, **without any warranty**! It may glitch, break, or spontaneously combust at any time. You have been warned!

**WARNING: Python 2 is no longer supported in the SupyPlugins *master* branch as of August 2017. Please migrate your bots to Python 3, or use the *python2-legacy* branch instead.**

## Installation
The recommended way of fetching plugins in this repository is to clone the git repository:

* `$ git clone https://github.com/jlu5/SupyPlugins`

and add the folder to your bot's `config directories.plugins`.

**You will need a working copy of [Limnoria](https://github.com/ProgVal/Limnoria) running on Python 3.4+.** Python 2 users should consult the *python2-legacy* branch in Git instead. Anything older will *not* work.

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
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### LastFM
- LastFM plugin, forked from [krf/supybot-lastfm](https://github.com/krf/supybot-lastfm).

##### MCInfo
- Fetches information from [minecraft.gamepedia.com](https://minecraft.gamepedia.com/).
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### [Namegen](Namegen/README.md)
- A small random name generator.

##### [NoTrigger](NoTrigger/README.md)
- Anti-abuse script; prevents the bot from triggering other bots by modifying its output slightly. For more information, see [NoTrigger/README.md](NoTrigger/README.md).

##### [NuWeather](NuWeather/README.md)
- A weather plugin for Limnoria. It supports [Dark Sky](https://darksky.net) and [Apixu](https://www.apixu.com/) as backends.

##### [OperUp](OperUp/README.md)
- Allows Supybot to oper up on configured networks, automatically (on connect) and on demand.

##### PassGen
- Generates random passwords on the fly!

##### [PkgInfo](PkgInfo/README.md)
- Fetches package information from various Linux and BSD distros' software repositories.
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### QuakeNet
- Log in to Quakenet's Q Service via CHALLENGEAUTH. This plugin was written by request and not officially supported.

##### Restart
- **EXPERIMENTAL**: provides a command to restart Limnoria from IRC.

##### [RelayNext](RelayNext/README.md)
- Next generation relayer plugin, designed with two-way relays in mind.

##### RhymeZone
- Fetches rhymes from http://rhymezone.com/.
   - **Requires:** [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/)

##### SedRegex
- History replacer using sed-style expressions. Fork of [t3chguy's Replacer plugin](https://github.com/t3chguy/Limnoria-Plugins/tree/master/Replacer).

##### SupyMisc
- Some assorted commands that don't seem to fit anywhere else.

##### SysDNS
- An alternative to Supybot's built-in DNS function, using the `host` DNS lookup utility on the host machine.
    * **Requires:** `host` DNS lookup binary (as in `/usr/bin/host`)

##### [TranslateParty](TranslateParty/README.md)
- Translates text through Google Translate multiple times in order to get amusing results.

##### Voteserv
- A plugin for storing and manipulating votes/polls.

##### [Weather](Weather/README.md) **[DEPRECATED]**
- My fork of [reticulatingspline's Weather](https://github.com/reticulatingspline/Weather) plugin, with rewritten output handling, explicit location search, and many other tweaks.
- **Update 2018012**: Weather Underground is shutting down free weather access, so this plugin will no longer be maintained. See the NuWeather plugin in this folder for an alternative using other backends.

##### Wikifetch
- Fork of [ProgVal's Wikipedia plugin](https://github.com/ProgVal/Supybot-plugins), with support for other wikis (via a `--site` option) and other improvements.
   - **Requires:** [lxml](https://lxml.de/installation.html)
