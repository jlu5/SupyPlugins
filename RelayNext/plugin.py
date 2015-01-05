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

import supybot.world as world
import supybot.irclib as irclib
import supybot.ircmsgs as ircmsgs
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('RelayNext')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

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
             self.log.warning('RelayNext: Unable to write pickled database: %s', e)

    def __init__(self, irc):
        self.__parent = super(RelayNext, self)
        self.__parent.__init__(irc)
        # We need to create a dict of the networks we're connected to and their
        # associated IRC objects, so we know where our messages should go
        self.networks = {}
        self.log.debug("RelayNext network index: %s" % self.networks)
        # This part is partly taken from the Relay plugin, and is used to
        # keep track of quitting users. Since quit messages aren't
        # channel-specific, we need to keep a cached copy of our IRC state
        # file and look at that to find whether we should send a quit
        # message through the relay. The conventional check for
        # 'irc.state.channels[channel]' won't work either,
        # because the user in question has already quit.
        self.ircstates = {}
        self.lastmsg = {}

        self.db = {}
        self.loadDB()
        world.flushers.append(self.exportDB)
        self.initializeNetworks()

    def die(self):
        self.exportDB()
        world.flushers.remove(self.exportDB)
        self.__parent.die()

    ### Relayer core

    def simpleHash(self, s):
        """<text>

        Returns a colorized version of <text> based on a simple hash algorithm
        (sum of all characters)."""
        colors = ("05", "04", "03", "09", "02", "12", "06", "13", "10", "11",
                  "07")
        num = 0
        for i in s:
            num += ord(i)
        num = num % len(colors)
        return "\x03%s%s\x03" % (colors[num], s)

    # This part keeps track of the IrcStates as mentioned above
    def __call__(self, irc, msg):
        if irc not in self.ircstates:
            self.ircstates[irc] = irclib.IrcState()
        try:
            self.ircstates[irc].addMsg(irc, self.lastmsg[irc])
        except KeyError:
            self.ircstates[irc].addMsg(irc,
                                       ircmsgs.ping("placeholder message"))
        finally:
            self.lastmsg[irc] = msg
        self.__parent.__call__(irc, msg)

    def initializeNetworks(self):
        for IRC in world.ircs:
            self.networks[IRC.network.lower()] = IRC

    def _getAllRelaysForNetwork(self, irc):
        """Returns all the relays a network is involved with."""
        network = irc.network.lower()
        results = []
        for relay in self.db.values():
            for cn in relay:
                cn = cn.split("@")
                if cn[1] == network:
                    results.append(cn[0])
        return results

    def _format(self, irc, msg):
        s = ''
        nick = msg.nick
        userhost = ''
        noHighlight = True
        useHostmask = True
        color = True
        channel = msg.args[0]
        netname = irc.network.lower()

        if color:
            nick = self.simpleHash(nick)
            netname = self.simpleHash(netname)
        if noHighlight:
            nick = '-' + nick
        # Skip hostmask checking if the sender is a server
        # ('.') present in name
        if useHostmask and '.' not in nick:
            try:
                userhost = ' (%s)' % msg.prefix.split('!', 1)[1]
            except:
                pass

        if msg.command == 'NICK':
            newnick = msg.args[0]
            if color:
                newnick = self.simpleHash(newnick)
            s = '- %s is now known as %s' % (nick, newnick)
        elif msg.command == 'PRIVMSG':
            s = '<%s> %s' % (nick, msg.args[1])
        elif msg.command == 'JOIN':
            s = '- %s%s has joined %s' % (nick, userhost, channel)
        elif msg.command == 'PART':
            # Part message isn't a required field and can be empty sometimes
            try:
                partmsg = ' (%s)' % msg.args[1]
            except:
                partmsg = ''
            s = '- %s%s has left %s%s' % (nick, userhost, channel, partmsg)
        elif msg.command == 'QUIT':
            s = '- %s has quit (%s)' % (nick, msg.args[0])
        elif msg.command == 'MODE':
            modes = ' '.join(msg.args[1:])
            s = '- %s%s set mode %s on %s' % (nick, userhost, modes, channel)

        if s:  # Add the network name and some final touch-ups
            s = "\x02[%s]\x02 %s" % (netname, s)
            s = s.replace("- -", "-", 1)
        return s

    def relay(self, irc, msg, channel=None):
        channel = channel or msg.args[0]
        # Get the source channel
        source = "%s@%s" % (channel, irc.network)
        source = source.lower()
        for relay in self.db.values():
            if source in relay:  # If our channel is in a relay
                # Create a copy of the relay definition so we don't
                # overwrite it
                targets = set(relay[:])
                # Remove the current channel so we we don't get a loop
                # of messages being relayed back to source
                targets.remove(source)
                for cn in targets:
                    target, net = cn.split("@")
                    if net not in self.networks.keys():
                        self.initializeNetworks()
                    try:
                        otherIrc = self.networks[net]
                    except KeyError:
                        self.log.debug("RelayNext: message to %s dropped, we "
                                      "are not connected there!", net)
                    else:
                        out_s = self._format(irc, msg)
                        if out_s:
                            out_msg = ircmsgs.privmsg(target, out_s)
                            out_msg.tag('relayedMsg')
                            otherIrc.queueMsg(out_msg)

    def doPrivmsg(self, irc, msg):
        self.relay(irc, msg)

    doJoin = doPart = doKick = doMode = doPrivmsg

    # NICK and QUIT aren't channel specific, so they require a bit
    # of extra handling
    def doNick(self, irc, msg):
        newnick = msg.args[0]
        for channel in self._getAllRelaysForNetwork(irc):
            if newnick in irc.state.channels[channel].users:
                self.relay(irc, msg, channel=channel)
    def doQuit(self, irc, msg):
        for channel in self._getAllRelaysForNetwork(irc):
            if msg.nick in self.ircstates[irc].channels[channel].users:
                self.relay(irc, msg, channel=channel)

    def outFilter(self, irc, msg):
        # Catch our own messages and send them into the relay (this is
        # useful because Supybot is often a multi-purpose bot!)
        if msg.command == 'PRIVMSG' and not msg.relayedMsg:
                if msg.args[0] in self._getAllRelaysForNetwork(irc):
                    new_msg = deepcopy(msg)
                    new_msg.nick = irc.nick
                    self.relay(irc, new_msg, channel=msg.args[0])
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
            self.log.warning('RelayNext: %s on %s attempted to view'
                             ' nicks in %s without being in it.', msg.nick,
                             irc.network, channel)
            irc.error(('You are not in %s.' % channel), Raise=True)

        source = "%s@%s" % (channel, irc.network)
        source = source.lower()
        totalChans = 0
        allUsers = []
        # Make a set to prevent duplicates since one channel
        # can be part of many relays
        Relays = set()
        for relay in self.db.values():
            if source in relay:
                for cn in relay:
                    Relays.add(cn)

        for cn in Relays:
            totalChans += 1
            channel, net = cn.split("@", 1)
            try:
                c = self.networks[net].state.channels[channel]
            except KeyError:
                continue
            totalUsers = len(c.users)
            users = []
            for s in c.users:
                s = s.strip()
                if s in c.ops:
                    users.append('@%s' % s)
                elif s in c.halfops:
                    users.append('%%%s' % s)
                elif s in c.voices:
                    users.append('+%s' % s)
                else:
                    users.append(s)
            allUsers += c.users
            s = format('%s users in %s on %s: %L', totalUsers,
                       channel, net, users)
            if 'count' not in opts:
                irc.reply(s, private=True)
        if 'count' in opts:
            irc.reply(totalUsers)
        else:
            irc.reply("Total users across %d channels: %d. Unique nicks: %d" %
                      (totalChans, totalUsers, len(set(allUsers))),
                      private=True)
    nicks = wrap(nicks, ['Channel', getopts({'count': ''})])

    def set(self, irc, msg, args, rid, relays):
        """<id> <relays>

        Sets relay <id> to relay between <relays>. <relays> is a space
        separated list of #channel@network combinations, where network is the
        NAME of your network (see 'networks' for a list of connected ones).
        <id> is the name of your relay; it can be a number, string, etc.
        """
        relays = set(relays)
        if len(relays) < 2:
            irc.error("Not enough channels to relay between (need at least "
                      "2).", Raise=True)

        for relay in relays:
            r = relay.split("@")
            if len(r) != 2 or not (ircutils.isChannel(r[0]) and r[1]):
                irc.error("Channels must be given in the form "
                          "#channel@networkname", Raise=True)
        else:
            self.db[rid] = [relay.lower() for relay in relays]
            irc.replySuccess()
    set = wrap(set, ['admin', 'somethingWithoutSpaces',
                     many('somethingWithoutSpaces')])

    def unset(self, irc, msg, args, rid):
        """<id>

        Removes relay <id>.
        """
        try:
            del self.db[rid]
        except KeyError:
            irc.error("No such relay '%s' exists." % rid, Raise=True)
        else:
            irc.replySuccess()
    unset = wrap(unset, ['admin', 'somethingWithoutSpaces'])

    def list(self, irc, msg, args):
        """takes no arguments.

        Lists all relays currently configured."""
        items = [format("%s: %s", ircutils.bold(k), ' \x02<=>\x02 '.join(v))
                 for (k, v) in self.db.items()]
        if not items:
            irc.error("No relays have been defined.", Raise=True)
        irc.reply(', '.join(items))

    def clear(self, irc, msg, args):
        """<takes no arguments.

        Clears all relays defined.
        """
        self.db = {}
        irc.replySuccess()
    clear = wrap(clear, ['admin'])

Class = RelayNext


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
