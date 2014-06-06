# SupyPlugins
### GLolol's collection of Supybot plugins

This repository includes forks/mods of existing Supybot plugins and some that I've written myself. All of the code in this repository is considered **experimental** and **not** ready for production use. It may glitch, break, or spontaneously combust at any time. You have been warned!

*Note:* This repository is currently being written for Python 2.7, and has *not* been tested for compatibility with other Python versions (that includes Python 3.x). I cannot guarantee that these plugins will work!

## Support
If you have any questions, concerns, or feature requests, please feel free to submit an issue. 

Or, you can find me on IRC at: ``irc.overdrive.pw #dev`` ([webchat](http://webchat.overdrive.pw/?channels=dev))

## List of plugins
Please note that this list may not always be up to date; your best bet is to actually browse the code for yourself!

Any specific plugin dependencies *should* also be listed.

##### Hostmasks *(deprecated)*
- Hostmasks plugin, allows one to fetch appropriate banmasks for users. Now deprecated due to a silly design flaw that made the plugin less efficient than it should've been.
  
##### Isup
- Provides a simple command to check whether a website is up or down (using [isup.me](http://isup.me)).

##### LinkRelay
- Mod of the [LinkRelay](https://github.com/ProgVal/Supybot-plugins/tree/master/LinkRelay) plugin. Originally designed for use with [OVERdrive-IRC](http://overdrive.pw/), with a few extra features such as a configurable list of nicks for the relayer to ignore. No longer in active development.

##### NoTrigger
- Anti-abuse script; modifies outFilter to prevent triggering other bots.

##### OperUp
- Simple plugin that allows Supybot to oper up on configured networks, automatically (on connect) and manually.

##### PassGen
- Generates passwords on the fly!

##### SupyMisc
- Some assorted commands that don't seem to fit anywhere else.

##### SysDNS
- An alternative to Supybot's built-in DNS function, using DNS lookup utilities (such as host or dig) available on the host machine.

##### TLDInfo
- Fetches TLD information using IANA's database (http://www.iana.org/domains/root/db/).
