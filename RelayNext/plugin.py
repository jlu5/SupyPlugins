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

    def set(self, irc, msg, args, rid, relays):
        """<id> <relays>
        
        Sets relay <id> to relay between <relays>. <relays> is a space separated list
        of #channel@network combinations, where network is the NAME of your network
        (see 'networks' for a list of connected ones).
        """
        relays = set(relays)
        if len(relays) < 2:
            irc.error("Not enough channels to relay between (need at least 2).", Raise=True)
        
        for relay in relays:
            r = relay.split("@")
            if len(r) != 2 or not (ircutils.isChannel(r[0]) and r[1]):
                irc.error("Channels must be given in the form #channel@networkname", Raise=True)
        else:
            self.db[rid] = [relay.lower() for relay in relays]
            irc.replySuccess()
    set = wrap(set, ['admin', 'positiveInt', many('somethingWithoutSpaces')])

    def unset(self, irc, msg, args, rid):
        """<id>
        
        Removes relay <id>.
        """
        try:
            del self.db[rid]
        except KeyError:
            irc.error("No such Relay with ID %s exists." % cid, Raise=True)
        else:
            irc.replySuccess()
    unset = wrap(unset, ['admin', 'positiveInt'])
    
    def list(self, irc, msg, args):
        """takes no arguments.
        
        Lists all relays currently configured."""
        items = [format("%s: %s", k, ' \x02<=>\x02 '.join(v)) for (k, v) in self.db.items()]
        if not items:
            irc.error("No relays have been defined.", Raise=True)
        irc.reply(format('%L', items))

    ### Relayer core

    def simpleHash(self, s):
        colors = ("05", "04", "03", "09", "02", "12",
                  "06", "13", "10", "11", "07")
        num = 0
        for i in s:
            num += ord(i)
        num = num % len(colors)
        return colors[num]

    '''def __call__(self, irc, msg):
        if irc not in self.ircstates:
            self.ircstates[irc] = irclib.IrcState()
            if irc.afterConnect:
                for channel in irc.state.channels:
                    irc.queueMsg(ircmsgs.who(channel))
        try:
            network = irc.network.lower()
            self.ircstates[network].addMsg(irc, self.lastmsg[network])
        except KeyError:
            pass
        finally:
            self.lastmsg[network] = msg
        self.__parent.__call__(irc, msg)'''

    def initializeNetworks(self):
        for IRC in world.ircs:
            self.networks[IRC.network] = IRC

    def _getAllRelaysForNetwork(self, network):
        network = network.lower()
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
        channel = None
        
        if ircutils.isChannel(msg.args[0]):
            channel = msg.args[0]

        if color:
            nick = "\x03%s%s\x03" % (self.simpleHash(nick), nick)
        if noHighlight:
            nick = '-' + nick
        if useHostmask and channel:
            userhost = ' (%s)' % msg.prefix.split('!', 1)[1]

        if msg.command == 'NICK':
            newnick = msg.args[0]
            for c in self._getAllRelaysForNetwork(irc.network):
                if newnick in irc.state.channels[c].users:
                    if color:
                        newnick = "\x03%s%s\x03" % (self.simpleHash(newnick), newnick)
                    s = '- %s is now known as %s' % (nick, newnick)
                    break
        elif msg.command == 'PRIVMSG':
            s = '<%s> %s' % (nick, msg.args[1])
        elif msg.command == 'JOIN':
            s = '- %s%s has joined %s' % (nick, userhost, channel)
        elif msg.command == 'PART':
            partmsg = ''
            # Part message isn't a required field and can be empty sometimes
            try:
                partmsg = ' (%s)' % msg.args[1]
            except:
                pass
            s = '- %s%s has parted %s%s' % (nick, userhost, channel, partmsg)
        # QUIT and NICK aren't specific to any channel, so they're harder
        # to parse
        elif msg.command == 'QUIT':
            for channel in self.ircstates[irc].channels:
                if msg.nick in channel.users:
                    s = '- %s has quit (%s)' % (nick, msg.args[0])
                    break
        return s
    
    def relay(self, irc, msg):
        netname = irc.network.lower()
        channel = msg.args[0]
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
                for chan in targets:
                    cn = chan.split("@")
                    if cn[1] not in self.networks.keys():
                        self.initializeNetworks()
                    otherIrc = self.networks[cn[1]]
                    targetchannel = cn[0]
                    out_s = self._format(irc, msg)
                    self.log.debug('RelayNext: message on %s would go to: %s', source, chan)
                    if out_s:
                        out_s = "\x02[%s]\x02 %s" % (netname, out_s)
                        otherIrc.queueMsg(ircmsgs.privmsg(targetchannel, out_s))

    def doPrivmsg(self, irc, msg):
        self.relay(irc, msg)
        
    doJoin = doPart = doKick = doQuit = doNick = doPrivmsg

Class = RelayNext


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
