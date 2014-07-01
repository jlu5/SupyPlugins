A fork of the LinkRelay plugin, tailored to my needs.

#### Differences from [stock LinkRelay](https://github.com/ProgVal/Supybot-plugins/tree/master/LinkRelay):

* Ignore nicks feature.
* Batch add (`addall`)/remove (`removeall`) feature for relays with more than 2 networks.
* `List` and `nicks` now reply in multiple messages instead of one large message.

#### Differences between my LinkRelay build:
Due to changes in the configuration variables, this plugin was renamed to RelayLink and is no longer compatible with LinkRelay.

* `colors` configuration group removed in favour of colour hashing for nicks.
* Added annoucing of relay disconnects/connects.
* `nicks` now has a `--count` option for channel statistics.
