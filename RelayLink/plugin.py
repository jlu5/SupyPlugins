###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
# Copyright (c) 2013-2014, James Lu (GLolol)
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

import re
import copy
import itertools
import supybot.log as log
import supybot.conf as conf
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.irclib as irclib
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.registry as registry
import supybot.callbacks as callbacks
from supybot.utils.structures import TimeoutQueue
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('RelayLink')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

@internationalizeDocstring
class RelayLink(callbacks.Plugin):
    # noIgnore = True
    threaded = True

    class Relay():
        def __init__(self, sourceChannel, sourceNetwork, targetChannel,
                     targetNetwork, channelRegex, networkRegex, messageRegex):
            self.sourceChannel = sourceChannel
            self.sourceNetwork = sourceNetwork
            self.targetChannel = targetChannel
            self.targetNetwork = targetNetwork
            self.channelRegex = channelRegex
            self.networkRegex = networkRegex
            self.messageRegex = messageRegex
            self.hasTargetIRC = False
            self.hasSourceIRCChannels = False

    def __init__(self, irc):
        self.__parent = super(RelayLink, self)
        self.__parent.__init__(irc)
        self._loadFromConfig()
        self.ircstates = {}
        for IRC in world.ircs:
            self.addIRC(IRC)
        floodProtectTimeout = conf.supybot.plugins.RelayLink.antiflood.seconds
        self.nonPrivmsgCounter = TimeoutQueue(floodProtectTimeout)
        self.privmsgCounter = TimeoutQueue(floodProtectTimeout)
        self.floodActivated = False
        try:
            conf.supybot.plugins.RelayLink.substitutes.addCallback(
                    self._loadFromConfig)
            conf.supybot.plugins.RelayLink.relays.addCallback(
                    self._loadFromConfig)
        except registry.NonExistentRegistryEntry:
            log.error("Your version of Supybot is not compatible with "
                      "configuration hooks. So, RelayLink won't be able "
                      "to reload the configuration if you use the Config "
                      "plugin.")

    def _loadFromConfig(self, name=None):
        self.relays = []
        for relay in self.registryValue('relays').split(' || '):
            if relay.endswith('|'):
                relay += ' '
            relay = relay.split(' | ')
            if not len(relay) == 5:
                continue
            try:
                self.relays.append(self.Relay(relay[0],
                                          relay[1],
                                          relay[2],
                                          relay[3],
                                          re.compile('^%s$' % relay[0], re.I),
                                          re.compile('^%s$' % relay[1]),
                                          re.compile(relay[4])))
            except:
                log.error('Failed adding relay: %r' % relay)

        self.nickSubstitutions = {}
        for substitute in self.registryValue('substitutes').split(' || '):
            if substitute.endswith('|'):
                substitute += ' '
            substitute = substitute.split(' | ')
            if not len(substitute) == 2:
                continue
            self.nickSubstitutions[substitute[0]] = substitute[1]

    def simpleHash(self, s):
        colors = ["05", "04", "03", "09", "02", "12",
                  "06", "13", "10", "11", "07"]
        num = 0
        for i in s:
            num += ord(i)
        num = num % 11
        return colors[num]

    def floodDetect(self):
        if self.registryValue("antiflood.announce") and not self.floodActivated:
            msgs = self.registryValue("antiflood.nonPrivmsgs")
            secs = self.registryValue("antiflood.seconds")
            s = ("%(network)s*** Flood detected ({msgs} non-PRIVMSG messages in {secs} seconds). Not relaying messages"
                " for {secs} seconds!".format(secs=secs, msgs=msgs))
            self.floodActivated = True
            return s
        else:
            return

    def getPrivmsgData(self, channel, nick, text, colored):
        if self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.privmsgs") > 0 and \
            (len(self.privmsgCounter) > self.registryValue("antiflood.privmsgs")):
            if self.registryValue("antiflood.announce") and not self.floodActivated:
                msgs = self.registryValue("antiflood.privmsgs")
                secs = self.registryValue("antiflood.seconds")
                s = ("%(network)s*** Flood detected ({msgs} messages in {secs} seconds). Not relaying messages"
                    " for {secs} seconds!".format(secs=secs, msgs=msgs)), {}
                self.floodActivated = True
                return s
            else:
                return
        self.floodActivated = False
        color = self.simpleHash(nick)
        nickprefix = ''
        if nick in self.nickSubstitutions:
            nick = self.nickSubstitutions[nick]
        if not self.registryValue('nicks', channel):
            nick = ''
        elif self.registryValue('noHighlight', channel):
            nickprefix = '-'
        if re.match('^\x01ACTION .*\x01$', text):
            text = text.strip('\x01')
            text = text[ 7 : ]
            if colored:
                return ('%(network)s* %(nickprefix)s\x03%(color)s%(nick)s\x03 %(text)s',
                        {'nick': nick, 'color': color, 'text': text,
                        'nickprefix': nickprefix})
            else:
                return ('%(network)s* %(nickprefix)s%(nick)s %(text)s',
                        {'nick': nick, 'text': text, 'nickprefix': nickprefix})
        else:
            if colored:
                return ('%(network)s<%(nickprefix)s\x03%(color)s%(nick)s\x03> %(text)s',
                        {'color': color, 'nick': nick, 'text': text,
                        'nickprefix': nickprefix})
            else:
                return ('%(network)s<%(nickprefix)s%(nick)s> %(text)s',
                        {'nick': nick, 'text': text, 'nickprefix': nickprefix})
        return s

    @internationalizeDocstring
    def list(self, irc, msg, args):
        """takes no arguments

        Returns all the defined relay links."""
        if irc.nested:
            irc.error('This command cannot be nested.', Raise=True)
        elif not self.relays:
            irc.reply(_('This is no relay enabled. Use "RelayLink add" "RelayLink'
                ' addall" to add one.'))
            return
        for relay in self.relays:
            if relay.hasTargetIRC:
                hasIRC = 'Link healthy!'
            else:
                hasIRC = '\x0302IRC object not scraped yet.\017'
            s ='\x02%s\x02 on \x02%s\x02 ==> \x02%s\x02 on \x02%s\x02.  %s'
            if not self.registryValue('color', msg.args[0]):
                s = s.replace('\x02', '')
            irc.reply(s %
                        (relay.sourceChannel,
                         relay.sourceNetwork,
                         relay.targetChannel,
                         relay.targetNetwork,
                         hasIRC), private=True)

    def doPrivmsg(self, irc, msg):
        self.addIRC(irc)
        self.privmsgCounter.enqueue([0])
        channel = msg.args[0]
        s = msg.args[1]
        s, args = self.getPrivmsgData(channel, msg.nick, s,
                               self.registryValue('color', channel))
        if channel not in irc.state.channels: # in private
            # cuts off the end of commands, so that passwords
            # won't be revealed in relayed PM's
            if callbacks.addressed(irc.nick, msg):
                if self.registryValue('color', channel):
                    color = '\x0314'
                    match = '(>\017 \w+) .*'
                else:
                    color = ''
                    match = '(> \w+) .*'
                s = re.sub(match, '\\1 %s[%s]' % (color, _('truncated')), s)
            s = '(via PM) %s' % s
        self.sendToOthers(irc, channel, s, args, isPrivmsg=True)

    def outFilter(self, irc, msg):
        if msg.command == 'PRIVMSG':
            if not msg.relayedMsg:
                if msg.args[0] in irc.state.channels:
                    s, args = self.getPrivmsgData(msg.args[0], irc.nick, msg.args[1],
                                    self.registryValue('color', msg.args[0]))
                    self.sendToOthers(irc, msg.args[0], s, args, isPrivmsg=True)
        return msg

    def doPing(self, irc, msg):
        self.addIRC(irc)

    def doMode(self, irc, msg):
        self.addIRC(irc)
        self.nonPrivmsgCounter.enqueue([0])
        args = {'nick': msg.nick, 'channel': msg.args[0],
                'mode': ' '.join(msg.args[1:]), 'userhost': ''}
        if self.registryValue("noHighlight", msg.args[0]):
            args['nick'] = '-'+msg.nick
        if self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.nonprivmsgs") > 0 and \
            (len(self.nonPrivmsgCounter) > self.registryValue("antiflood.nonprivmsgs")):
            s = self.floodDetect()
            if s:
                self.sendToOthers(irc, msg.args[0], s, args)
                self.floodActivated = True
            else: return
        else:
            self.floodActivated = False
            if self.registryValue('color', msg.args[0]):
                args['nick'] = '\x03%s%s\x03' % (self.simpleHash(msg.nick), args['nick'])
            if self.registryValue('hostmasks', msg.args[0]) and "." not in \
                msg.nick:
                args['userhost'] = ' (%s@%s)' % (msg.user, msg.host)
            s = ('%(network)s%(nick)s%(userhost)s set mode %(mode)s on'
                 ' %(channel)s')
            self.sendToOthers(irc, msg.args[0], s, args)

    def doJoin(self, irc, msg):
        args = {'nick': msg.nick, 'channel': msg.args[0], 'userhost': ''}
        if self.registryValue("noHighlight", msg.args[0]):
            args['nick'] = '-'+msg.nick
        self.nonPrivmsgCounter.enqueue([0])
        if irc.nick == msg.nick:
            if self.registryValue('color'):
                s = '%(network)s\x0309*** Relay joined to %(channel)s'
            else:
                s = '%(network)s*** Relay joined to %(channel)s'
        elif self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.nonprivmsgs") > 0 and \
            (len(self.nonPrivmsgCounter) > self.registryValue("antiflood.nonprivmsgs")):
            s = self.floodDetect()
            if s:
                self.sendToOthers(irc, msg.args[0], s, args)
                self.floodActivated = True
            else: return
        else:
            self.floodActivated = False
            if self.registryValue('color', msg.args[0]):
                args['nick'] = '\x03%s%s\x03' % (self.simpleHash(msg.nick), args['nick'])
            if self.registryValue('hostmasks', msg.args[0]):
                args['userhost'] = ' (%s@%s)' % (msg.user, msg.host)
            s = '%(network)s%(nick)s%(userhost)s has joined %(channel)s'
        self.addIRC(irc)
        self.sendToOthers(irc, msg.args[0], s, args)

    def doPart(self, irc, msg):
        self.nonPrivmsgCounter.enqueue([0])
        args = {'nick': msg.nick, 'channel': msg.args[0], 'message': '',
                'userhost': ''}
        if self.registryValue("noHighlight", msg.args[0]):
            args['nick'] = '-'+msg.nick
        if self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.nonprivmsgs") > 0 and \
            (len(self.nonPrivmsgCounter) > self.registryValue("antiflood.nonprivmsgs")):
            s = self.floodDetect()
            if s:
                self.sendToOthers(irc, msg.args[0], s, args)
                self.floodActivated = True
            else: return
        else:
            self.addIRC(irc)
            self.floodActivated = False
            if self.registryValue('color', msg.args[0]):
                args['nick'] = '\x03%s%s\x03' % (self.simpleHash(msg.nick), args['nick'])
            if self.registryValue('hostmasks', msg.args[0]):
                args['userhost'] = ' (%s@%s)' % (msg.user, msg.host)
            try:
                args['message'] = ' (%s)' % (msg.args[1])
            except IndexError:
                pass
            s = '%(network)s%(nick)s%(userhost)s has parted %(channel)s%(message)s'
            self.sendToOthers(irc, msg.args[0], s, args)

    def doKick(self, irc, msg):
        self.addIRC(irc)
        args = {'kicked': msg.args[1], 'channel': msg.args[0],
                'kicker': msg.nick, 'message': msg.args[2], 'userhost': ''}
        self.nonPrivmsgCounter.enqueue([0])
        if self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.nonprivmsgs") > 0 and \
            (len(self.nonPrivmsgCounter) > self.registryValue("antiflood.nonprivmsgs")):
            s = self.floodDetect()
            if s:
                self.sendToOthers(irc, msg.args[0], s, args)
                self.floodActivated = True
            return
        self.floodActivated = False
        if self.registryValue('color', msg.args[0]):
            args['kicked'] = '\x03%s%s\x03' % (self.simpleHash(msg.args[1]), args['kicked'])
        if self.registryValue('hostmasks', msg.args[0]):
            # The IRC protocol only sends the hostmask of the kicker, so we'll need
            # to use an alternate method to fetch the host of the person being
            # kicked. (in this case, using ircutils)
            h = ircutils.splitHostmask(irc.state.nickToHostmask(msg.args[1]))
            args['userhost'] = ' (%s@%s)' % (h[1], h[2])
        s = ('%(network)s%(kicked)s%(userhost)s has been kicked from '
             '%(channel)s by %(kicker)s (%(message)s)')
        self.sendToOthers(irc, msg.args[0], s, args)

    def doNick(self, irc, msg):
        self.addIRC(irc)
        if self.registryValue("noHighlight"):
            args = {'oldnick': '-'+msg.nick, 'newnick': '-'+msg.args[0]}
        else:
            args = {'oldnick': msg.nick, 'newnick': msg.args[0]}
        self.nonPrivmsgCounter.enqueue([0])
        if self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.nonprivmsgs") > 0 and \
            (len(self.nonPrivmsgCounter) > self.registryValue("antiflood.nonprivmsgs")):
            s = self.floodDetect()
            if s:
                self.sendToOthers(irc, msg.args[0], s, args)
                self.floodActivated = True
        else:
            if self.registryValue('color'):
                args['oldnick'] = '\x03%s%s\x03' % (self.simpleHash(msg.nick), args['oldnick'])
                args['newnick'] = '\x03%s%s\x03' % (self.simpleHash(msg.args[0]), args['newnick'])
            s = '%(network)s%(oldnick)s is now known as %(newnick)s'
            self.floodActivated = False
            for (channel, c) in irc.state.channels.iteritems():
                if msg.args[0] in c.users:
                    self.sendToOthers(irc, channel, s, args)

    def doQuit(self, irc, msg):
        args = {'nick': msg.nick, 'message': msg.args[0]}
        if self.registryValue("noHighlight"): args['nick'] = '-' + msg.nick
        self.nonPrivmsgCounter.enqueue([0])
        if msg.nick == irc.nick: # It's us.
            if self.registryValue('color'):
                s = '%(network)s\x0304*** ERROR: Relay disconnected...'
            else:
                s = '%(network)s*** ERROR: Relay disconnected...'
        elif self.registryValue("antiflood.enable") and \
            self.registryValue("antiflood.nonprivmsgs") > 0 and \
            (len(self.nonPrivmsgCounter) > self.registryValue("antiflood.nonprivmsgs")):
            s = self.floodDetect()
            if s:
                self.sendToOthers(irc, msg.args[0], s, args)
                self.floodActivated = True
        else:
            if self.registryValue('color'):
                args['nick'] = '\x03%s%s\x03' % (self.simpleHash(msg.nick), args['nick'])
            s = '%(network)s%(nick)s has quit (%(message)s)'
            self.floodActivated = False
        self.sendToOthers(irc, None, s, args, msg.nick)
        self.addIRC(irc)

    def sendToOthers(self, irc, channel, s, args, nick=None, isPrivmsg=False):
        assert channel is not None or nick is not None
        def format_(relay, s, args):
            if 'network' not in args:
                if self.registryValue('includeNetwork', relay.targetChannel):
                    if self.registryValue('color', relay.targetChannel):
                        args['network'] = "\x02[\x03%s%s\x03]\x02 " % \
                            (self.simpleHash(irc.network), irc.network)
                    else:
                        args['network'] = "[%s] " % irc.network
                    if not isPrivmsg and not self.registryValue("noHighlight", channel):
                        args['network'] += "- "
                else:
                    args['network'] = ''
            return s % args
        def send(s):
            if not relay.hasTargetIRC:
                self.log.info('RelayLink:  IRC %s not yet scraped.' %
                              relay.targetNetwork)
            elif relay.targetIRC.zombie:
                self.log.info('RelayLink:  IRC %s appears to be a zombie'%
                              relay.targetNetwork)
            elif irc.isChannel(relay.targetChannel) and \
                    relay.targetChannel not in relay.targetIRC.state.channels:
                self.log.info('RelayLink:  I\'m not in in %s on %s' %
                              (relay.targetChannel, relay.targetNetwork))
            else:
                if isPrivmsg or \
                        self.registryValue('nonPrivmsgs', channel) == 'privmsg':
                    msg = ircmsgs.privmsg(relay.targetChannel, s)
                elif self.registryValue('nonPrivmsgs', channel) == 'notice':
                    msg = ircmsgs.notice(relay.targetChannel, s)
                else:
                    return
                msg.tag('relayedMsg')
                relay.targetIRC.sendMsg(msg)

        if channel is None:
            for relay in self.relays:
                if not relay.hasSourceIRCChannels:
                    continue
                for channel in relay.sourceIRCChannels:
                    new_s = format_(relay, s, args)
                    if nick in relay.sourceIRCChannels[channel].users and \
                            relay.channelRegex.match(channel) and \
                            relay.networkRegex.match(irc.network)and \
                            relay.messageRegex.search(new_s):
                        send(new_s)
        else:
            for relay in self.relays:
                new_s = format_(relay, s, args)
                if relay.channelRegex.match(channel) and \
                        relay.networkRegex.match(irc.network)and \
                        relay.messageRegex.search(new_s):
                    send(new_s)

    def addIRC(self, irc):
        match = False
        for relay in self.relays:
            if relay.sourceNetwork == irc.network:
                relay.sourceIRCChannels = copy.deepcopy(irc.state.channels)
                relay.hasSourceIRCChannels = True
            if relay.targetNetwork == irc.network and not relay.hasTargetIRC:
                relay.targetIRC = irc
                relay.hasTargetIRC = True

    @internationalizeDocstring
    def nicks(self, irc, msg, args, channel, optlist):
        """[<channel>] [--count]

        Returns the nicks of the people in the linked channels.
        <channel> is only necessary if the message
        isn't sent on the channel itself.
        If --count is specified, only the amount of """
        keys = [option for (option, arg) in optlist]
        if irc.nested and 'count' not in keys:
            irc.error('This command cannot be nested.', Raise=True)
        if msg.nick not in irc.state.channels[channel].users:
            self.log.warning('RelayLink: %s on %s attempted to view'
                ' nicks in %s without being in it.'
                % (msg.nick, irc.network, channel))
            irc.error(('You are not in %s.' % channel), Raise=True)
        # Include the local channel for nicks output
        c = irc.state.channels[channel]
        totalUsers = len(c.users)
        totalChans = 1
        users = []
        for s in c.users:
            s = s.strip()
            if not s:
                continue
            if s in c.ops:
                users.append('@%s' % s)
            elif s in c.halfops:
                users.append('%%%s' % s)
            elif s in c.voices:
                users.append('+%s' % s)
            else:
                users.append(s)
        s = _('%d users in %s on %s:  %s') % (totalUsers,
            channel, irc.network,
            utils.str.commaAndify(users))
        if 'count' not in keys: irc.reply(s, private=True)
        for relay in self.relays:
            if relay.sourceChannel == channel and \
                    relay.sourceNetwork == irc.network:
                totalChans += 1
                if not relay.hasTargetIRC:
                    irc.reply(_('I haven\'t scraped the IRC object for %s '
                              'yet. Try again in a minute or two.') % \
                              relay.targetNetwork)
                else:
                    users = []
                    ops = []
                    halfops = []
                    voices = []
                    normals = []
                    numUsers = 0
                    target = relay.targetChannel

                    channels = relay.targetIRC.state.channels
                    found = False
                    for key, channel_ in channels.items():
                        #if re.match(relay.targetChannel, key):
                        if ircutils.toLower(relay.targetChannel) \
                            == ircutils.toLower(key):
                            found = True
                            break
                    if not found:
                        continue

                    for s in channel_.users:
                        s = s.strip()
                        if not s:
                            continue
                        numUsers += 1
                        totalUsers += 1
                        if s in channel_.ops:
                            users.append('@%s' % s)
                        elif s in channel_.halfops:
                            users.append('%%%s' % s)
                        elif s in channel_.voices:
                            users.append('+%s' % s)
                        else:
                            users.append(s)
                    #utils.sortBy(ircutils.toLower, ops)
                    #utils.sortBy(ircutils.toLower, halfops)
                    #utils.sortBy(ircutils.toLower, voices)
                    #utils.sortBy(ircutils.toLower, normals)
                    users.sort()
                    msg.tag('relayedMsg')
                    s = _('%d users in %s on %s:  %s') % (numUsers,
                            relay.targetChannel,
                            relay.targetNetwork,
                            utils.str.commaAndify(users))
                    if 'count' not in keys: irc.reply(s, private=True)
        if not irc.nested: 
            irc.reply("Total users across %d channels: %d. " % \
                (totalChans, totalUsers), private=False if 'count' in keys else True)
        else:
            irc.reply(totalUsers)
        irc.noReply()
    nicks = wrap(nicks, ['Channel', getopts({'count':''})])

    # The following functions handle configuration
    def _writeToConfig(self, from_, to, regexp, add):
        from_, to = from_.split('@'), to.split('@')
        args = from_
        args.extend(to)
        args.append(regexp)
        s = ' | '.join(args)

        currentConfig = self.registryValue('relays')
        if add == True:
            if s in currentConfig.split(' || '):
                return False
            if currentConfig == '':
                self.setRegistryValue('relays', value=s)
            else:
                self.setRegistryValue('relays',
                                      value=' || '.join((currentConfig,s)))
        else:
            newConfig = currentConfig.split(' || ')
            if s not in newConfig:
                return False
            newConfig.remove(s)
            self.setRegistryValue('relays', value=' || '.join(newConfig))
        return True

    def _parseOptlist(self, irc, msg, tupleOptlist, batchadd=False):
        optlist = {}
        for key, value in tupleOptlist:
            optlist.update({key: value})
        if not batchadd:
            if 'from' not in optlist and 'to' not in optlist:
                irc.error(_('You must give at least --from or --to.'))
                return
            for name in ('from', 'to'):
                if name not in optlist:
                    optlist.update({name: '%s@%s' % (msg.args[0], irc.network)})
            if 'reciprocal' in optlist:
                optlist.update({'reciprocal': True})
            else:
                optlist.update({'reciprocal': False})
            if not len(optlist['from'].split('@')) == 2:
                irc.error(_('--from should be like "--from #channel@network"'))
                return
            if not len(optlist['to'].split('@')) == 2:
                irc.error(_('--to should be like "--to #channel@network"'))
                return
        if 'regexp' not in optlist:
            optlist.update({'regexp': ''})
        return optlist

    @internationalizeDocstring
    def add(self, irc, msg, args, optlist):
        """[--from <channel>@<network>] [--to <channel>@<network>] [--regexp <regexp>] [--reciprocal]

        Adds a relay to the list. You must give at least --from or --to; if
        one of them is not given, it defaults to the current channel@network.
        Only messages matching <regexp> will be relayed; if <regexp> is not
        given, everything is relayed.
        If --reciprocal is given, another relay will be added automatically,
        in the opposite direction."""
        optlist = self._parseOptlist(irc, msg, optlist)
        if optlist is None:
            return

        failedWrites = 0
        if not self._writeToConfig(optlist['from'], optlist['to'],
                                   optlist['regexp'], True):
            failedWrites += 1
        if optlist['reciprocal']:
            if not self._writeToConfig(optlist['to'], optlist['from'],
                                       optlist['regexp'], True):
                failedWrites += 1

        self._loadFromConfig()
        if failedWrites == 0:
            irc.replySuccess()
        else:
            irc.error(_('One (or more) relay(s) already exists and has not '
                        'been added.'))
    add = wrap(add, [('checkCapability', 'admin'),
                     getopts({'from': 'something',
                              'to': 'something',
                              'regexp': 'something',
                              'reciprocal': ''})])

    def addall(self, irc, msg, args, optlist, channels):
        """[--regexp <regexp>] <channel1@network1> <channel2@network2> [<channel3@network3>] ...
        
        Batch adds all the relays/reciprocals between the channels defined. Useful if you are
        relaying to more than 2 networks/channels with one bot, as a large amount of
        reciprocals easily becomes a mess.
        Only messages matching <regexp> will be relayed; if <regexp> is not
        given, everything is relayed."""
        optlist = self._parseOptlist(irc, msg, optlist, batchadd=True)
        channels = channels.split()
        if len(channels) < 2:
            irc.error('Not enough channels specified to relay! (needs at least 2)', Raise=True)
        if len(channels) > self.registryValue('addall.max'):
            irc.error('Too many channels specified, aborting. (see config plugins.RelayLink.addall.max)', Raise=True)
        for ch in channels:
            if len(ch.split("@")) != 2: 
                irc.error("Channels must be specified in the format #channel@network", Raise=True)
        failedWrites = writes = 0
        # Get all the channel combinations and try to add them one by one
        p = itertools.permutations(channels, 2)
        for c in p:
            if not self._writeToConfig(c[0], c[1],
                                   optlist['regexp'], True):
                failedWrites += 1
                if self.registryValue('logFailedChanges'):
                    self.log.warning("RelayLink: failed to batch add relay: {} -> {}".format(c[0],c[1]))
            writes += 1
        self._loadFromConfig()
        if failedWrites == 0:
            irc.replySuccess()
        else:
            irc.reply('Finished, though {} out of {} relays failed to be added.'.format(failedWrites, writes))
    addall = wrap(addall, [('checkCapability', 'admin'),
                     getopts({'regexp': 'something'}), 'text'])
                     
    def removeall(self, irc, msg, args, optlist, channels):
        """[--regexp <regexp>] <channel1@network1> [<channel2@network2>] [<channel3@network3>] ...
        
        Batch removes relays. If only one channel@network is given, removes all
        relays going to and from the channel.
        Otherwise, removes all relays going between the channels defined (similar to addall)."""
        optlist = self._parseOptlist(irc, msg, optlist, batchadd=True)
        channels = channels.split()
        if len(channels) > self.registryValue('addall.max'):
            irc.error('Too many channels specified, aborting. (see config plugins.RelayLink.addall.max)', Raise=True)
        failedWrites = writes = 0
        for ch in channels:
            if len(ch.split("@")) != 2: 
                irc.error("Channels must be specified in the format #channel@network", Raise=True)
        if len(channels) == 1:
            c = tuple(channels[0].split('@'))
            for relay in self.relays:
                # semi-hack channel matching; not sure if there's a better way to do this
                if c[0] == relay.sourceChannel and c[1] == relay.sourceNetwork:
                    s = "%s@%s" % (relay.targetChannel, relay.targetNetwork)
                    if not self._writeToConfig(channels[0], s,
                        optlist['regexp'], False):
                        # This shouldn't really ever error, but we'll keep it just in case
                        failedWrites += 1
                        if self.registryValue('logFailedChanges'):
                            self.log.warning("RelayLink: failed to batch remove relay: {} -> {}".format(c[0],c[1]))
                    writes += 1
                elif c[0] == relay.targetChannel and c[1] == relay.targetNetwork:
                    s = "%s@%s" % (relay.sourceChannel, relay.sourceNetwork)
                    if not self._writeToConfig(s, channels[0],
                        optlist['regexp'], False):
                        failedWrites += 1
                        if self.registryValue('logFailedChanges'):
                            self.log.warning("RelayLink: failed to batch remove relay: {} -> {}".format(c[0],c[1]))
                    writes += 1
            if writes == 0:
                irc.error("No matching relays for %s found." % channels[0], Raise=True)
        elif len(channels) >= 2:
            # Get all the channel combinations and try to remove them one by one
            p = itertools.permutations(channels, 2)
            for c in p:
                if not self._writeToConfig(c[0], c[1],
                                       optlist['regexp'], False):
                    failedWrites += 1
                    if self.registryValue('logFailedChanges'):
                        self.log.warning("RelayLink: failed to batch remove relay: {} -> {}".format(c[0],c[1]))
                writes += 1
        self._loadFromConfig()
        if failedWrites == 0:
            irc.replySuccess()
        else:
            irc.reply('Finished, though {} out of {} relays failed to be removed.'.format(failedWrites, writes))
    removeall = wrap(removeall, [('checkCapability', 'admin'),
                     getopts({'regexp': 'something'}), 'text'])

    @internationalizeDocstring
    def remove(self, irc, msg, args, optlist):
        """[--from <channel>@<network>] [--to <channel>@<network>] [--regexp <regexp>] [--reciprocal]

        Remove a relay from the list. You must give at least --from or --to; if
        one of them is not given, it defaults to the current channel@network.
        Only messages matching <regexp> will be relayed; if <regexp> is not
        given, everything is relayed.
        If --reciprocal is given, another relay will be removed automatically,
        in the opposite direction."""
        optlist = self._parseOptlist(irc, msg, optlist)
        if optlist is None:
            return

        failedWrites = 0
        if not self._writeToConfig(optlist['from'], optlist['to'],
                                   optlist['regexp'], False):
            failedWrites += 1
        if optlist['reciprocal']:
            if not self._writeToConfig(optlist['to'], optlist['from'],
                                       optlist['regexp'], False):
                failedWrites +=1

        self._loadFromConfig()
        if failedWrites == 0:
            irc.replySuccess()
        else:
            irc.error(_('One (or more) relay(s) did not exist and has not '
                        'been removed.'))
    remove = wrap(remove, [('checkCapability', 'admin'),
                     getopts({'from': 'something',
                              'to': 'something',
                              'regexp': 'something',
                              'reciprocal': ''})])

    def _getSubstitutes(self):
        # Get a list of strings
        substitutes = self.registryValue('substitutes').split(' || ')
        if substitutes == ['']:
            return {}
        # Convert it to a list of tuples
        substitutes = [tuple(x.split(' | ')) for x in substitutes]
        # Finally, make a dictionnary
        substitutes = dict(substitutes)

        return substitutes

    def _setSubstitutes(self, substitutes):
        # Get a list of tuples from the dictionnary
        substitutes = substitutes.items()
        # Make it a list of strings
        substitutes = ['%s | %s' % (x,y) for x,y in substitutes]
        # Finally, get a string
        substitutes = ' || '.join(substitutes)

        self.setRegistryValue('substitutes', value=substitutes)

    @internationalizeDocstring
    def substitute(self, irc, msg, args, regexp, to):
        """<regexp> <replacement>

        Replaces all nicks that matches the <regexp> by the <replacement>
        string."""
        substitutes = self._getSubstitutes()
        # Don't check if it is already in the config: if will be overriden
        # automatically and that is a good thing.
        substitutes.update({regexp: to})
        self._setSubstitutes(substitutes)
        self._loadFromConfig()
        irc.replySuccess()
    substitute = wrap(substitute, [('checkCapability', 'admin'),
                                   'something',
                                   'text'])

    @internationalizeDocstring
    def nosubstitute(self, irc, msg, args, regexp):
        """<regexp>

        Undo a substitution."""
        substitutes = self._getSubstitutes()
        if regexp not in substitutes:
            irc.error(_('This regexp was not in the nick substitutions '
                        'database'))
            return
        # Don't check if it is already in the config: if will be overriden
        # automatically and that is a good thing.
        substitutes.pop(regexp)
        self._setSubstitutes(substitutes)
        self._loadFromConfig()
        irc.replySuccess()
    nosubstitute = wrap(nosubstitute, [('checkCapability', 'admin'),
                                       'something'])
    def rpm(self, irc, msg, args, remoteuser, otherIrc, text):
        """<remoteUser> <network> <text>

        Sends a private message to a user on a remote network."""
        found = found2 = False
        if not self.registryValue("remotepm.enable"):
            irc.error("This command is not enabled; please set 'config plugins.relaylink.remotepm.enable' "
                "to True.", Raise=True)
        for relay in self.relays:
            channels = otherIrc.state.channels
            for key, channel_ in channels.items():
                if ircutils.toLower(relay.targetChannel) \
                    == ircutils.toLower(key) and remoteuser in channel_.users:
                    found = True
                    break
            for ch in irc.state.channels:
                if ircutils.toLower(relay.sourceChannel) == \
                    ircutils.toLower(ch) and msg.nick in irc.state.channels[ch].users:
                    found2 = True
                    break
        if found and found2:
            prefix = msg.prefix if self.registryValue("remotepm.useHostmasks") else msg.nick
            if self.registryValue("remotepm.useNotice"):
                otherIrc.queueMsg(ircmsgs.notice(remoteuser, "Message from %s on %s: %s" % (prefix, irc.network, text)))
            else:
                otherIrc.queueMsg(ircmsgs.privmsg(remoteuser, "Message from %s on %s: %s" % (prefix, irc.network, text)))
        else:
            irc.error("User '%s' does not exist on %s or you are not sharing "
                "a channel with them." % (remoteuser, otherIrc.network), Raise=True)
    rpm = wrap(rpm, ['nick', ('networkIrc', True), 'text'])

Class = RelayLink

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
