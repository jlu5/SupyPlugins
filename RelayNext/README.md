**RelayNext** is a next generation relayer system for Supybot, designed with two-way relays in mind. It is intended as a replacement for the stock Relay plugin, and an alternative to the LinkRelay plugin.

RelayNext supports relaying between channels with different names, and stores its entries in a database, preventing corruption from being stored in the config.

## Usage

### Creating a new relay

Creating a relay is simple, simply run:

* `relaynext add Your-relay-name #channel1@networkOne #somewhere@networkTwo`

on your bot. **You must specify a name for the relay! (replacing `your-relay-name` with whatever)**

### Modifying relays

Once a relay is created, you can manipulate these entries further using the `set`, `add`, and `remove` commands.

* `relaynext add Your-relay-name #somewhere@overTheRainbow`
* `relaynext remove Your-relay-name #channel1@networkOne`

Relays are case-insensitive and require at least two channels to relay between. When the last two channels are removed, the relay is automatically deleted.

Note: The `set` command **replaces** the relay in question, while `add` **adds** channels to it. Both will create a new relay if the name you specify doesn't already exist.

### Listing defined relays

The `list` command will list all relays defined.

* `relaynext list`

### Removing/clearing relays

You can remove relays (or channels within them) using the `remove` command. There is also a `clear` command which clears all relays.

To remove channels from an existing relay:

* `relaynext remove Your-relay-name #channel1@networkone #blah@networktwo`

Or, to delete an entire relay:

* `relaynext remove Your-relay-name`

Relays require at least two channels to relay between. When the last two channels are removed, the relay is automatically deleted.

## Configuration

Most of the following options are also configurable per channel. For any channel-specific variables, settings on the target relay channel are used for NICK and QUIT messages, while settings on the source channel are applied for all others. This is because nick changes and quits are effectively channel-independent.

### Relaying non-PRIVMSG events

RelayNext supports relaying the following non-PRIVMSG events: joins, kicks, mode changes, nick changes, parts, quits, and topic changes. Each of these can be turned on and off using configuration variables, and have the following defaults:

- `config plugins.RelayNext.events.relayjoins`: `True`
- `config plugins.RelayNext.events.relaykicks`: `True`
- `config plugins.RelayNext.events.relaymodes`: `True`
- `config plugins.RelayNext.events.relaynicks`: `True`
- `config plugins.RelayNext.events.relayparts`: `True`
- `config plugins.RelayNext.events.relayquits`: `True`
- `config plugins.RelayNext.events.relaytopics`: `False`

Note: Topic relaying will only show topic *changes* in a channel. **It does not, and can not sync topics between channels!**

### Ignoring users
RelayNext uses Supybot's built in ignore system. However, you can set which messages you want to ignore (from ignored users) using `config plugins.RelayNext.events.userignored`.

This key takes a space separated list, and defaults to ignoring `PRIVMSG` and `MODE`. **If you want to disable the ignore feature entirely, simply set this value blank: `config plugins.RelayNext.events.userignored ""`**

### Highlight prevention
One annoying aspect of relays is that when someone is on multiple relayed channels with the same nick, they will be spammed with highlights whenever they speak. RelayNext can mitigate this behavior (**for some clients**) by prefixing all nicks with a hyphen (`-`). Of course, this behavior is not universal and can't be made to magically silence highlights for all clients, and you may be better off looking for an "ignore highlight from certain nicks" feature for your IRC client.

You can turn this prefixing on via:
* `config plugins.RelayNext.noHighlight True`

### Flood prevention *(experimental)*
RelayNext has experimental flood prevention built in, though it's not quite reliable yet. When flood prevention is triggered, a warning message is displayed and all further messages of the matched type will be ignored for a certain amount of seconds. 

For example, in the event of a join flood, JOIN messages are blocked from being relayed, while other messages are still displayed. This can be useful in the event of a netsplit on a large network, to prevent the bot from flooding itself off, while still allowing conversations to be mostly unaffected.

To turn it on:
* `config plugins.RelayNext.antiflood.enable True`

You can then configure various the various options below:

* `plugins.RelayNext.antiflood.maximum`: configure the maximum amount of messages (PRIVMSGs) allowed in *X* seconds before flood prevention is triggered.
* `plugins.RelayNext.antiflood.seconds`: configure the *X* amount of seconds mentioned above.
* `plugins.RelayNext.antiflood.timeout`: determines the amount of seconds the bot will wait before flood prevention expires (messages are relayed as normal again).

### Toggling colors and hostmask display

You can enable/disable colors via the configuration variable `plugins.RelayNext.color`, and hostmask display via `plugins.RelayNext.hostmasks`.
