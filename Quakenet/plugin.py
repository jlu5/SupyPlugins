###
# Copyright (c) 2004, Jeremiah Fincher
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
import hashlib
import hmac
import sys

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Quakenet')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

def isQuakeNet(irc, msg, args, state):
    if irc.state.supported.get('NETWORK') != 'QuakeNet':
        irc.error('It seems like you\'re not on QuakeNet.  '
                  'This plugin should only be used on QuakeNet.', Raise=True)

addConverter('isQuakeNet', isQuakeNet)

class Quakenet(callbacks.Plugin):
    """Supports authentication to Quakenet's Q Services."""
    threaded = True

    def _isQuakeNet(self, irc):
        return irc.state.supported.get('NETWORK') == 'QuakeNet'

    def __init__(self, irc):
        self.__parent = super(Quakenet, self)
        self.__parent.__init__(irc)
        self.lastChallenge = None
        self.toQ = 'Q@CServe.quakenet.org'
        self.fromQ = 'Q!TheQBot@CServe.quakenet.org'

    def outFilter(self, irc, msg):
        if self._isQuakeNet(irc) and msg.command == 'PRIVMSG' and \
                msg.args[0] in ('NickServ', 'ChanServ'):
            self.log.info('Filtering outgoing message to '
                          'non-QuakeNet services.')
            return None
        return msg

    def do376(self, irc, msg):
        if self._isQuakeNet(irc):
            self._doAuth(irc, msg)

    def _doAuth(self, irc, msg):
        name = self.registryValue('authname')
        password = self.registryValue('password')
        if name and password:
            self._sendToQ(irc, 'challenge')
        else:
            irc.error('Username and/or password are not set.')

    def doNotice(self, irc, msg):
        if self._isQuakeNet(irc) and msg.prefix == self.fromQ:
            self._doQ(irc, msg)

    def _handleChallenge(self, irc, digest, challenge):
        # Using https://www.quakenet.org/development/challengeauth
        # as of 15 Mar 2015.
        name = self.registryValue('authname')
        name = ircutils.toLower(name, casemapping='rfc1459').encode('ascii')
        password = self.registryValue('password')
        password = password[:10].encode('ascii')
        passdigest = hashlib.md5(password).hexdigest().encode('ascii')
        key = hashlib.md5(name + b':' + passdigest).hexdigest().encode('ascii')
        digestf = getattr(hashlib, digest.split('HMAC-', 1)[1].lower())
        response = hmac.new(key, challenge.encode('ascii'), digestf).hexdigest()
        self._sendToQ(irc, 'challengeauth %s %s %s' % (name.decode('ascii'),
                      response, digest))

    def _doQ(self, irc, msg):
        self.log.debug('Received %r from Q.', msg)
        payload = msg.args[1]
        # Challenge/response.
        if 'already requested a challenge' in payload:
            self.log.debug('Received "already requested challenge" from Q.')
            assert self.lastChallenge
            self._handleChallenge(irc, *self.lastChallenge)
        elif 'successfully' in payload:
            # This needs to be before the next one since it also starts with
            # "CHALLENGE"
            self.log.info('%s: Received %s from Q.', irc.network, payload)
        elif payload.startswith('CHALLENGE'):
            self.log.info('%s: Received CHALLENGE from Q.', irc.network)
            challenge = payload.split()[1]
            digest = 'HMAC-MD5'
            if digest not in payload:
                irc.error('Q is not supporting our authentication method; '
                          'this plugin needs to be updated!', Raise=True)
            self.lastChallenge = (digest, challenge)
            self._handleChallenge(irc, digest, challenge)
        elif payload.startswith('Remember:'):
            self.log.info('%s: CHALLENGE authentication successful.',
                          irc.network)
        else:
            self.log.warning('Unexpected message from Q: %r', msg)

    def _sendToQ(self, irc, s):
        m = ircmsgs.privmsg(self.toQ, s)
        self.log.debug('Sending %r to Q.', m)
        irc.sendMsg(m)

    def q(self, irc, msg, args, text):
        """<text>

        Sends <text> to Q.
        """
        self._sendToQ(irc, text)
        irc.noReply()
    q = wrap(q, ['owner', 'isQuakeNet', 'text'])

    def auth(self, irc, msg, args):
        """takes no arguments

        Attempts to authenticate with Q.
        """
        self._doAuth(irc, msg)
        irc.noReply()
    auth = wrap(auth, ['owner', 'isQuakeNet'])

Class = Quakenet


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
