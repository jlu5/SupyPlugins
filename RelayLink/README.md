A fork of the LinkRelay plugin, tailored to my needs.

#### Differences from [stock LinkRelay](https://github.com/ProgVal/Supybot-plugins/tree/master/LinkRelay):

* Ignore nicks feature.
* Batch add (`addall`)/remove (`removeall`) feature for relays with more than 2 networks.
* `list` and `nicks` now reply in multiple messages instead of one large message.
* Configurable remote PM command for users (disabled by default but can be enabled using `config plugins.relaylink.remotepm.enable 1`
* `colors` configuration group removed in favour of colour hashing for nicks.
* Added annoucing of relay disconnects/connects.
* `nicks` now has a `--count` option for channel statistics.
