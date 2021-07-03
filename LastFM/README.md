LastFM for Supybot/Limnoria
==============

A Supybot/Limnoria plugin for LastFM, forked from [krf/supybot-lastfm](https://github.com/krf/supybot-lastfm).

### Changes made in this fork

- Native Python 3 support.
- Code cleanup, formatting enhancements, and various bugfixes.
- Migration to the newer (v2) LastFM API, using JSON instead of XML.
- Simpler DB implementation tracking bot accounts and hostmasks instead of nicks (unfortunately, this resets your DB if you're upgrading from krf's older versions).
- Only the `np` and `profile` commands are present - the others have since been broken by LastFM API changes and thus were removed.
- Optional integration with the DDG plugin in this repository, to provide YouTube links for tracks if available. Enable `plugins.LastFM.fetchYouTubeLink` for this to work.

### Setup and Usage

Before using any parts of this plugin, you must register on the LastFM website and obtain an API key for your bot: http://www.last.fm/api/account/create

After doing so, you must then configure your bot to use your key: `/msg <botname> config plugins.LastFM.apiKey <your-api-key>`.

Showing now playing information:
```
<@jlu5> %np RJ
<@Atlas> RJ listened to Apache by The Shadows [Back To Back] at 01:42 PM, October 10, 2015
```

Showing profile information:
```
<@jlu5> %profile RJ
<@Atlas> RJ (realname: Richard Jones) registered on 03:50 AM, November 20, 2002; age: 0 / m; Country: United Kingdom; Tracks played: 114896
```
