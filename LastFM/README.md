supybot-lastfm (GLolol's fork)
==============

[![Build Status](https://travis-ci.org/GLolol/supybot-lastfm.svg?branch=devel)](https://travis-ci.org/GLolol/supybot-lastfm)

A Supybot plugin for LastFM.

### Summary of changes:

- Native Python 3 support.
- Code cleanup and various bugfixes.
- Migration to a new LastFM API (v2).
- Simpler DB implementation using pickle and hostmasks instead of nicks (requires DB reset).
- Only `np` and `profile` commands - the others have since been broken by LastFM API changes and removed.

The full diff can be found [here](https://github.com/GLolol/supybot-lastfm/compare/krf:master...devel).

### Support
You may find me on IRC at `irc.overdrive.pw #dev` ([webchat](http://webchat.overdrive.pw/?channels=dev)).

Feel free to suggest enhancements on the [issue tracker](https://github.com/GLolol/supybot-lastfm/issues). Pull requests are welcome.

### Usage

Showing now playing information:
```
[09:53:33] $np
[09:53:34] KRF listened to “Behind Closed Doors” by Rise Against [The Sufferer & The Witness] more than 1 days ago
```

Showing profile information:
```
[09:53:36] $profile
[09:53:37] KRF (realname: Kevin Funk) registered on May 28, 2006; 23 years old / m; Country: Germany; Tracks played: 32870
```
