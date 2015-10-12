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

## Longer description/Backstory on why I wrote this
Sometimes when you have a public development channel with many bots residing in it, someone will come along and do something really evil: that is, create a huge message loop by chaining all your innocent bots together!

For example:

```
<evilperson> !echo @echo $echo &echo abcdefg
<bot1> @echo $echo &echo abcdefg
<bot2> $echo &echo abcdefg
<bot3> &echo abcdefg
...
```

NoTrigger aims to solve some of these issues by prepending messages that start with commonly-used bot triggers with a [zero-width space](https://en.wikipedia.org/wiki/Zero-width_space) or ZWSP. These are non-printing characters, which are essentially invisible to people's clients. (We're going to use a space to represent the ZWSP in the examples below, just so you can see a difference.)

For example:

```
<evilperson> !echo @echo $echo &echo abcdefg
<securedbot>  @echo $echo &echo abcdefg
...
```

Boom. Problem solved, right? Well, almost.

Some bots will also respond to their nick!

```
<evilperson> !echo bot2: echo bot3: echo i lost the game!
<bot1> bot2: echo bot3: echo i lost the game!
<bot2> bot3: echo i lost the game!
...
```

This is slightly harder to parse, so we have to check if a message matches `<something>: <text>` or `<something>, <text>` (where `<something>` can be used as the name of a bot).

OKAY OKAY, now our bot is really foolproof, right?

**ALMOST!** Then there are the truly evil ops (shoutout to [@jacob1](https://github.com/jacob1)) that start messing with your bot by introducing colour stripping! :D

Fortunately, we'll append these message with a space too! (when the channel is set to strip colours, of course.)

##### Before:
```
Channel is set +c.
<evilperson> !bold "bot2: echo bot3: echo i lost the game!"
<unsecuredbot> bot2: echo bot3: echo i lost the game!
<bot2> bot3: echo i lost the game!
...
```

##### After:

```
Channel is set +c.
<evilperson> !bold "bot2: echo bot3: echo i lost the game!"
<securedbot>  bot2: echo bot3: echo i lost the game!
```

That's all! Find any more ways to abuse a poor, innocent bot? Let me know on the issue tracker! :stuck_out_tongue_closed_eyes:

(and no, not all bots use a hostmask matching `*!*@*/bot/*`, not even on freenode!)
