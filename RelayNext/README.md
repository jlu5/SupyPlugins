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

Once a relay is created, you can remove the relays (or channels within them) using the `remove` command. There is also a `clear` command which clears all relays.

To remove channels from an existing relay:

* `relaynext remove Your-relay-name #channel1@networkone #blah@networktwo`

Or, to delete an entire relay:

* `relaynext remove Your-relay-name`

Relays require at least two channels to relay between. When the last two channels are removed, the relay is automatically deleted.

## Configuration
### Relaying non-PRIVMSG events

RelayNext supports relaying the following non-PRIVMSG events: joins, kicks, mode changes, nick changes, parts, quits, and topic changes. Each of these can be turned on and off using configuration variables, and have the following defaults:

- `config plugins.RelayNext.events.relayjoins`: True
- `config plugins.RelayNext.events.relaykicks`: True
- `config plugins.RelayNext.events.relaymodes`: True
- `config plugins.RelayNext.events.relaynicks`: True
- `config plugins.RelayNext.events.relayparts`: True
- `config plugins.RelayNext.events.relayquits`: True
- `config plugins.RelayNext.events.relaytopics`: False

Note: Topic relaying will only show topic *changes* in a channel. **It does not, and can not sync topics between channels!**
### Ignoring users
RelayNext uses Supybot's built in ignore system, but you can set which kinds of messages you want to ignore from ignored users using `config plugins.RelayNext.events.userignored`.

This key takes a space separated list, and defaults to ignoring `PRIVMSG` and `MODE`. **If you want to disable this ignore feature, simply set the value blank: `config plugins.RelayNext.events.userignored ""`**
