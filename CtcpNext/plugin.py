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

import supybot.utils as utils
import supybot.world as world
import supybot.ircmsgs as ircmsgs
import supybot.conf as conf
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('CtcpNext')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

filename = conf.supybot.directories.data.dirize("CtcpNext.db")

class CtcpNext(callbacks.PluginRegexp):
    """Alternative to the official Ctcp plugin, with configurable replies."""
    regexps = ("ctcp", "ctcpPing")

    def loadDB(self):
        try:
            with open(filename, 'rb') as f:
               self.db = pickle.load(f)
        except Exception as e:
            self.log.debug('CtcpNext: Unable to load pickled database: %s', e)

    def exportDB(self):
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self.db, f, 2)
        except Exception as e:
             self.log.warning('CtcpNext: Unable to write pickled database: %s', e)

    def __init__(self, irc):
        self.__parent = super(CtcpNext, self)
        self.__parent.__init__(irc)
        self.defaultdb = {'VERSION': '$version', 'TIME': '$now'}
        self.db = self.defaultdb
        self.loadDB()
        world.flushers.append(self.exportDB)

    def die(self):
        self.exportDB()
        world.flushers.remove(self.exportDB)
        self.__parent.die()

    def _reply(self, irc, msg, payload, s):
        if s:
            s = '\x01%s %s\x01' % (payload, s)
        else:
            s = '\x01%s\x01' % payload
        irc.queueMsg(ircmsgs.notice(msg.nick, s))

    def ctcpPing(self, irc, msg, match):
        "^\x01PING(?: (.+))?\x01$"
        self.log.info('CtcpNext: Received CTCP PING from %s', msg.prefix)
        payload = match.group(1) or ''
        self._reply(irc, msg, 'PING', payload)

    def ctcp(self, irc, msg, match):
        "^\x01(.*?)\x01$"
        payload = match.group(1)
        if payload:
            payload = payload.split()[0].upper()
            if payload in ('PING', 'ACTION'):
                return
            try:
                response = self.db[payload]
                response = ircutils.standardSubstitute(irc, msg, response)
                self._reply(irc, msg, payload, response)
                self.log.info('CtcpNext: Received CTCP %s from %s', payload,
                              msg.prefix)
            except KeyError:
                self.log.info('CtcpNext: Received unhandled CTCP %s from %s',
                              payload, msg.prefix)

    def set(self, irc, msg, args, ctcp, response):
        """<ctcp> <response>

        Sets the response for <ctcp> to <response>. Exceptions include
        ACTION and PING, which are handled accordingly. All the standard
        substitutes ($version, $now, $nick, etc.) are handled properly.
        """
        self.db[ctcp.upper()] = response
        irc.replySuccess()
    set = wrap(set, ['admin', 'somethingWithoutSpaces', 'text'])

    def unset(self, irc, msg, args, ctcp):
        """<ctcp>

        Unsets the response for <ctcp>.
        """
        ctcp = ctcp.upper()
        try:
            del self.db[ctcp]
        except KeyError:
            irc.error("No such CTCP '%s' exists." % ctcp, Raise=True)
        else:
            irc.replySuccess()
    unset = wrap(unset, ['admin', 'somethingWithoutSpaces'])

    def list(self, irc, msg, args):
        """takes no arguments.

        Lists the CTCP responses currently configured."""
        items = [format("%s: %s", k, ircutils.bold(v)) for (k, v) in self.db.items()]
        irc.reply(format('%L', items))

    def clear(self, irc, msg, args):
        """takes no arguments.

        Resets all custom CTCP responses to defaults."""
        self.db = self.defaultdb
        irc.replySuccess()

Class = CtcpNext


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
