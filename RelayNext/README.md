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

The `unset` command removes a relay name, while the `clear` command clears all relays. The `remove` command removes individual channels from a relay, deleting it completely when the amount of channels is less than 2.
