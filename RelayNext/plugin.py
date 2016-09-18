###
# Copyright (c) 2015, James Lu
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

from copy import deepcopy
import pickle
import re
import textwrap

import supybot.world as world
import supybot.irclib as irclib
import supybot.ircmsgs as ircmsgs
import supybot.ircdb as ircdb
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.utils.structures import TimeoutQueue
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('RelayNext')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


filename = conf.supybot.directories.data.dirize("RelayNext.db")

class RelayNext(callbacks.Plugin):
    """Next generation relayer plugin."""
    threaded = True
    noIgnore = True

    ### Database handling

    def loadDB(self):
        try:
            with open(filename, 'rb') as f:
               self.db = pickle.load(f)
        except Exception as e:
            self.log.debug('RelayNext: Unable to load pickled database: %s', e)

    def exportDB(self):
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self.db, f, 2)
        except Exception as e:
             self.log.warning('RelayNext: Unable to write pickled database: %s',
                              e)

    def __init__(self, irc):
        self.__parent = super(RelayNext, self)
        self.__parent.__init__(irc)

        # This part facilitates flood protection
        self.msgcounters = {}
        self.floodTriggered = {}

        self.db = {}
        self.loadDB()

        # Add our database exporter to world.flushers, so it's automatically
        # ran on every flush cycle.
        world.flushers.append(self.exportDB)

    def die(self):
        self.exportDB()
        world.flushers.remove(self.exportDB)
        self.__parent.die()

    ### Relayer core

    def simpleHash(self, s, hash_using=''):
        """
        Returns a colorized version of the given text based on a simple hash algorithm
        (sum of all characters).
        """
        colors = ('02', '03', '04', '05', '06', '07', '08', '09', '10', '11',
                  '12', '13')

        # Optionally specify a different string to hash vs. display
        hash_using = hash_using or s

        num = sum([ord(char) for char in hash_using])
        num = num % len(colors)
        return "\x03%s%s\x03" % (colors[num], s)

    def _format(self, irc, msg, channel, announcement=False):
        """
        Formats a relay given the IRC object, msg object, and channel.
        """
        s = ''
        nick = real_nick = msg.nick
        userhost = ''
        noHighlight = self.registryValue('noHighlight', channel)
        useHostmask = self.registryValue('hostmasks', channel)
        color = self.registryValue('color', channel)
        netname = irc.network

        # Adding a zero-width space to prevent being highlighted by clients
        if noHighlight:
            nick = (nick[0] + "\u200b" + nick[1:] if len(nick) > 0 else "")

        if color:
            nick = self.simpleHash(nick, hash_using=real_nick)
            netname = self.simpleHash(netname)

        # Skip hostmask checking if the sender is a server
        # (i.e. a '.' is present in their name)
        if useHostmask and '.' not in nick:
            try:
                userhost = ' (%s)' % msg.prefix.split('!', 1)[1]
            except:
                pass

        if announcement:
            # Announcements use a special syntax
            s = '*** %s' % announcement
        else:
            if msg.command == 'NICK':
                newnick = msg.args[0]
                if color:
                    newnick = self.simpleHash(newnick)

                if noHighlight:
                    newnick = '-' + newnick

                s = '%s is now known as %s' % (nick, newnick)

            elif msg.command == 'PRIVMSG':
                text = msg.args[1]

                # Show status prefixes (@%+) in front of the nick if enabled,
                # but only the highest prefix.
                if self.registryValue("showPrefixes", channel):
                    chobj = irc.state.channels[channel]
                    if chobj.isOp(real_nick):
                        nick = '@' + nick
                    elif chobj.isHalfop(real_nick):
                        nick = '%' + nick
                    elif chobj.isVoice(real_nick):
                        nick = '+' + nick

                # Check for CTCP ACTION and format those properly.
                if re.match('^\x01ACTION .*\x01$', text):
                    text = text[8:-1]
                    s = '* %s %s' % (nick, text)
                elif text.startswith('\x01'):
                    # Other CTCP messages should just be ignored
                    return
                else:
                    s = '<%s> %s' % (nick, msg.args[1])

            elif msg.command == 'JOIN':
                s = '%s%s has joined %s' % (nick, userhost, channel)

            elif msg.command == 'PART':
                # Part message isn't a required field and can be empty
                try:
                    partmsg = ' (%s)' % msg.args[1]
                except IndexError:
                    partmsg = ''

                s = '%s%s has left %s%s' % (nick, userhost, channel, partmsg)

            elif msg.command == 'QUIT':
                s = '%s has quit (%s)' % (nick, msg.args[0])

            elif msg.command == 'MODE':
                modes = ' '.join(msg.args[1:])
                s = '%s%s set mode %s on %s' % (nick, userhost, modes, channel)

            elif msg.command == 'TOPIC':
                s = '%s set topic on %s to: %s' % (nick, channel, msg.args[1])

            elif msg.command == 'KICK':
                kicked = msg.args[1]
                # Show the host of the kicked user, not the kicker
                userhost = irc.state.nickToHostmask(kicked).split('!', 1)[1]
                if color:
                    kicked = self.simpleHash(kicked)
                if noHighlight:
                    kicked = '-' + kicked
                s = '%s (%s) has been kicked from %s by %s (%s)' % (kicked,
                    userhost, channel, nick, msg.args[2])

        if s:  # Then, prepend the source network name in bold.
            s = "\x02[%s]\x02 %s" % (netname, s)
        return s

    def relay(self, irc, msg, channel=None):
        channel = (channel or msg.args[0]).lower()
        self.log.debug("RelayNext (%s): got channel %s", irc.network, channel)
        if not channel in irc.state.channels:
            return

        # Check for ignored events first. Checking for "'.' not in msg.nick" is for skipping
        # ignore checks from servers.
        ignoredevents = map(str.upper, self.registryValue('events.userIgnored', channel))
        if msg.command in ignoredevents and msg.nick != irc.nick and '.' not in msg.nick and\
                ircdb.checkIgnored(msg.prefix, channel):
            self.log.debug("RelayNext (%s): ignoring message from %s",
                           irc.network, msg.prefix)
            return

        # Get the source channel
        source = "%s@%s" % (channel, irc.network)
        source = source.lower()

        out_s = self._format(irc, msg, channel)
        if out_s:
            for relay in self.db.values():
                self.log.debug("RelayNext (%s): check if %s in %s", irc.network, source, relay)
                if source in relay:  # If our channel is in a relay
                    self.log.debug("RelayNext: found %s to be in relay %s", source, relay)

                    # Remove ourselves from the target channels so we don't get duplicated messages
                    targets = list(relay)
                    targets.remove(source)

                    self.log.debug("RelayNext: found targets %s for relay %s", targets, relay)

                    if self.registryValue("antiflood.enable", channel):
                        # Flood prevention timeout - how long commands of a certain type
                        # should cease being relayed after flood prevention triggers
                        timeout = self.registryValue("antiflood.timeout", channel)

                        # If <maximum> messages of the same kind on one channel is
                        # received in <seconds> seconds, flood prevention timeout is
                        # triggered.
                        maximum = self.registryValue("antiflood.maximum", channel)
                        seconds = self.registryValue("antiflood.seconds", channel)

                        # Store the message in a counter, with the keys taking the
                        # form of (source channel@network, command name). If the counter
                        # doesn't already exist, create one here.
                        try:
                            self.msgcounters[(source, msg.command)].enqueue(msg.prefix)
                        except KeyError:
                            self.msgcounters[(source, msg.command)] = TimeoutQueue(seconds)

                        # Two different limits: one for messages and one for all others
                        if msg.command == "PRIVMSG":
                            maximum = self.registryValue("antiflood.maximum", channel)
                        else:
                            maximum = self.registryValue("antiflood.maximum.nonPrivmsgs",
                                                         channel)

                        if len(self.msgcounters[(source, msg.command)]) > maximum:
                            # Amount of messages in the counter surpassed our limit,
                            # announce the flood and block relaying messages of the
                            # same type for X seconds
                            self.log.debug("RelayNext (%s): message from %s blocked by "
                                           "flood protection.", irc.network, channel)

                            if self.floodTriggered.get((source, msg.command)):
                                # However, only send the announcement once.
                                return

                            c = msg.command
                            e = format("Flood detected on %s (%s %ss/%s seconds), "
                                       "not relaying %ss for %s seconds!", channel,
                                       maximum, c, seconds, c, timeout)
                            out_s = self._format(irc, msg, channel, announcement=e)

                            self.floodTriggered[(source, msg.command)] = True
                            self.log.info("RelayNext (%s): %s", irc.network, e)
                        else:
                            self.floodTriggered[(source, msg.command)] = False

                    for cn in targets:
                        # Iterate over all the relay targets for this message:
                        # each target is stored internally as a #channel@netname
                        # string.
                        target, net = cn.split("@")
                        otherIrc = world.getIrc(net)
                        if otherIrc is None:
                            self.log.debug("RelayNext: message to network %r"
                                           " dropped, we are not connected "
                                           "there!", net)
                            return

                        target_chanobj = otherIrc.state.channels.get(target)
                        if (not target_chanobj) or otherIrc.nick not in target_chanobj.users:
                            # We're not in the target relay channel!
                            self.log.debug("RelayNext: message to %s@%s "
                                           "dropped, we are not in that "
                                           "channel!", target, net)
                        else:
                            out_msg = ircmsgs.privmsg(target, out_s)

                            # Tag the message as relayed so we (and other relayers) don't
                            # try to relay it again.
                            out_msg.tag('relayedMsg')
                            otherIrc.queueMsg(out_msg)

    def doPrivmsg(self, irc, msg):
        self.relay(irc, msg)

    def doNonPrivmsg(self, irc, msg):
        if self.registryValue("events.relay%ss" % msg.command, msg.args[0]):
            self.relay(irc, msg)

    doTopic = doPart = doKick = doMode = doJoin = doNonPrivmsg

    # NICK and QUIT aren't channel specific, so they require a bit
    # of extra handling
    def doNick(self, irc, msg):
        for channel in msg.tagged('channels'):
            if self.registryValue("events.relaynicks", channel):
                self.relay(irc, msg, channel=channel)

    def doQuit(self, irc, msg):
        for channel in msg.tagged('channels'):
            if self.registryValue("events.relayquits", channel):
                self.relay(irc, msg, channel=channel)

    def outFilter(self, irc, msg):
        # Catch our own messages and send them into the relay (this is
        # useful because Supybot is often a multi-purpose bot!)
        try:
            if msg.command == 'PRIVMSG' and not msg.relayedMsg:
                new_msg = deepcopy(msg)
                new_msg.nick = irc.nick
                self.relay(irc, new_msg, channel=msg.args[0])
        except Exception:
            # We want to log errors, but not block the bot's output
            log.exception("RelayNext: Caught error in outFilter:")
        finally:
            return msg

    ### User commands

    def nicks(self, irc, msg, args, channel, optlist):
        """[<channel>] [--count]
        Returns the nicks of the people in the linked channels.
        <channel> is only necessary if the message isn't sent in the channel
        itself.
        If --count is specified, only the amount of users in the relay is given."""
        opts = dict(optlist)

        if irc.nested and 'count' not in keys:
            irc.error('This command cannot be nested.', Raise=True)

        try:
            c = irc.state.channels[channel]
        except KeyError:
            irc.error("Unknown channel '%s'." % channel, Raise=True)

        if msg.nick not in c.users:
            self.log.warning('RelayNext: %s on %s attempted to view '
                             'nicks of %s without being in it.', msg.nick,
                             irc.network, channel)
            irc.error(("You are not in '%s'." % channel), Raise=True)

        source = "%s@%s" % (channel, irc.network)
        source = source.lower()
        channel_count = 0
        user_count = 0
        all_users = []

        # First, enumerate all the relays that the calling channel is it. Use a
        # set to prevent duplicates since one channel can be part of many relays.
        all_relays = set()
        for relay in self.db.values():
            if source in relay:
                for channelpair in relay:
                    # Each channel pair is a "#chan@net" string in the DB.
                    all_relays.add(channelpair)

        for channelpair in all_relays:
            channel_count += 1
            channel, net = channelpair.split("@", 1)
            try:
                c = world.getIrc(net).state.channels[channel]
            except (KeyError, AttributeError):
                # Unknown network or network disconnected.
                continue
            user_count += len(c.users)
            users = []

            # Sort users before listing them, but do so case-insensitively.
            for s in sorted(c.users, key=ircutils.toLower):
                s = s.strip()
                if s in c.ops:
                    users.append('@%s' % s)
                elif s in c.halfops:
                    users.append('%%%s' % s)
                elif s in c.voices:
                    users.append('+%s' % s)
                else:
                    users.append(s)

            all_users += c.users
            s = format('%s users in %s on %s: %L', len(c.users),
                       channel, net, users)

            # In outputting the user list, we need to make sure that the message fits,
            # and if not, wrap it into multiple messages.
            # XXX: This is ugly, but https://github.com/ProgVal/Limnoria/issues/1080
            # means we have to chop off the (XX more messages) part too.
            allowed_length = 466 - len(irc.prefix) - len(irc.nick) - len(msg.nick) - \
                len(_('(XX more messages)'))
            replies = textwrap.wrap(s, allowed_length)

            if 'count' not in opts:
                # Only bother doing this if we're not using --count.
                irc.reply(replies[0], private=True, notice=True)
                for s in replies[1:]:
                    irc.reply("... %s" % s, private=True, notice=True)

        if 'count' in opts:  # --count was specified; just reply with the amount of users.
            irc.reply(user_count)
        elif channel_count:
            irc.reply("Total users across %d channels: %d. Unique nicks: %d" %
                      (channel_count, user_count, len(set(all_users))),
                      private=True)
        else:
            irc.error("No relays for '%s' exist." % channel)
    nicks = wrap(nicks, ['Channel', getopts({'count': ''})])

    def checkRelays(self, irc, relays):
        for relay in relays:
            r = relay.split("@")
            if len(r) != 2 or not (ircutils.isChannel(r[0]) and r[1]):
                irc.error("Channels must be given in the form "
                          "#channel@networkname.", Raise=True)

    def set(self, irc, msg, args, rid, relays):
        """<relay name> <#channel1>@<network1> <#channel2>@<network2> [<#channel3>@<network3>] ...

        Sets <relay name> to relay between the specified channels,
        replacing it if it already exists. Each relay requires at least
        two channels to relay between.
        """
        relays = set(map(str.lower, relays))
        if len(relays) < 2:
            irc.error("Not enough channels to relay between (need at least "
                      "2).", Raise=True)
        self.checkRelays(irc, relays)
        self.db[rid] = relays
        irc.replySuccess()
    set = wrap(set, ['admin', 'somethingWithoutSpaces',
                     many('somethingWithoutSpaces')])

    def add(self, irc, msg, args, rid, relays):
        """<relay name> [<#channel1>@<network1>] [<#channel2>@<network2>] ...

        Adds the specified channels to an existing relay <relay name>,
        creating it if it does not already exist.
        """
        # Supybot's internals are terribly inconsistent here, only
        # returning a list IF there are more than one items. Otherwise,
        # the object is returned alone.
        if type(relays) == list:
            relays = set(map(str.lower, relays))
        else:
            relays = set([relays.lower()])
        self.checkRelays(irc, relays)
        if rid not in self.db.keys() and len(relays) < 2:
            irc.error("Not enough channels to relay between (need at least "
                      "2).", Raise=True)
        try:
            new_relays = set(self.db[rid])
        except KeyError:
            self.db[rid] = new_relays = set()
        new_relays.update(relays)
        self.db[rid] = new_relays
        irc.replySuccess()
    add = wrap(add, ['admin', 'somethingWithoutSpaces',
                     many('somethingWithoutSpaces')])

    def remove(self, irc, msg, args, rid, relays):
        """<relay name> [<#channel1>@<network1>] [<#channel2>@<network2>] ...

        Removes the specified channels from <relay name>. If no channels
        are given, removes the entire relay.
        """
        try:
            current_relays = self.db[rid]
        except KeyError:
            irc.error("No such relay '%s' exists." % rid, Raise=True)
        if not relays:
            del self.db[rid]
            irc.replySuccess()
            return
        relays = list(map(str.lower, relays))
        self.checkRelays(irc, relays)
        missing = []
        for relay in relays:
            if relay not in current_relays:
                missing.append(relay)
            current_relays.discard(relay)
        if len(current_relays) < 2:
            del self.db[rid]
        if missing:
            s = format("However, the following channels were not removed "
                       "because they were not found in the original relay: %L",
                       missing)
            irc.replySuccess(s)
            return
        irc.replySuccess()
    remove = wrap(remove, ['admin', 'somethingWithoutSpaces',
                           any('somethingWithoutSpaces')])

    def list(self, irc, msg, args):
        """takes no arguments.

        Lists all relays currently configured."""
        items = [format("%s: %s", ircutils.bold(k), ' \x02<=>\x02 '.join(v))
                 for (k, v) in self.db.items()]
        if not items:
            irc.error("No relays have been defined.", Raise=True)
        irc.reply(', '.join(items))

    def clear(self, irc, msg, args):
        """takes no arguments.

        Clears all relays defined.
        """
        self.db = {}
        irc.replySuccess()
    clear = wrap(clear, ['admin'])

Class = RelayNext


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
