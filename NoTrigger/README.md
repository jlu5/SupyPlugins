NoTrigger is an anti-abuse plugin that modifies outFilter to prevent triggering other bots.

## Short description
In short, NoTrigger works by:

 - Prepending messages that start with a symbol (```!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~```) or any configured prefixes with a [zero width space](https://en.wikipedia.org/wiki/Zero-width_space) (ZWSP), since these are often used as prefixes for bots. This has the effect of being completely invisible, and tricks most bots into ignoring yours!
 - Prepending messages with a ZWSP if the channel is set to block colors and a message begins with a formatting code (sneaky attackers can otherwise do something like `\x02!echo hello` to bypass filters).
 - Optionally, prepending messages with a ZWSP if they match `<something>: ` or `<something>, `, since some bots are taught to respond to their nicks.
 - Optionally, blocking all channel-wide CTCPs (except for ACTION).
 - Optionally, stripping the bell character from any outgoing messages.
 - Optionally, appending messages that end with any configured suffixes with a ZWSP.

To enable NoTrigger, set the `plugins.NoTrigger.enable` config option `True` for the channels in question. You can find a list of NoTrigger's options (toggling the things mentioned above) by running `config list plugins.NoTrigger`.

## Background with examples
Sometimes when you have a public development channel with many bots residing in it, someone will come along and do something really evil: chaining these bots together to create a huge message loop.

#### Before:

```
<evilperson> !echo @echo $echo &echo abcdefg
<bot1> @echo $echo &echo abcdefg
<bot2> $echo &echo abcdefg
<bot3> &echo abcdefg
...
```

NoTrigger aims to solve some of these issues by prepending messages that start with commonly-used bot triggers with a [zero-width space](https://en.wikipedia.org/wiki/Zero-width_space) (ZWSP). These are non-printing characters which are invisible on most clients, so the impact of the plugin is minimal. (The examples below will use space to represent the ZWSP, just so you can see a difference.)

#### After:

```
<evilperson> !echo @echo $echo &echo abcdefg
<securedbot>  @echo $echo &echo abcdefg
...
```

Problem solved, right?

Almost. Some bots will also respond to their nick!

```
<evilperson> !echo bot2: echo bot3: echo i lost the game!
<bot1> bot2: echo bot3: echo i lost the game!
<bot2> bot3: echo i lost the game!
...
```

This is slightly harder to parse, but we essentially check if a message matches `<something>: <text>` or `<something>, <text>` (where `<something>` can be anything, including the name of a bot).

Now our bot is really foolproof, right?

Almost! What about color stripping modes? We'll have to prepend matching messages with a space too if those are set...

#### Before:
```
Channel is set +c.
<evilperson> !bold "bot2: echo bot3: echo i lost the game!"
<unsecuredbot> bot2: echo bot3: echo i lost the game!
<bot2> bot3: echo i lost the game!
...
```

#### After:

```
Channel is set +c.
<evilperson> !bold "bot2: echo bot3: echo i lost the game!"
<securedbot>  bot2: echo bot3: echo i lost the game!
```
