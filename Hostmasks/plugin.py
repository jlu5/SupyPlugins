###
# Copyright (c) 2013-2014, GLolol (GLolol1@hotmail.com)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# * Neither the name of the software nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import re
import socket
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Hostmasks')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class Hostmasks(callbacks.Plugin):
    """The Hostmasks plugin allows one to retrieve idents, hostnames, and 
    banmasks for users, useful for nested commands."""
    threaded = True
    
    def _SplitHostmask(self, irc, nick):
        # Split the hostmask into 3 sections: nick, ident, and host.
        try: 
            splithostmask = ircutils.splitHostmask(irc.state.nickToHostmask(nick))
        except KeyError:
            irc.error('There is no such nick \'%s\'.' % nick, Raise=True)
        return splithostmask
    
    def _isv4IP(self, ipstr):
        try:
            socket.inet_aton(ipstr)
            return True
        except socket.error:
            return False
            
    def _isv4cloak(self, hostname):
        # Smart bans: look for charybdis-style IP cloaks, Unreal/InspIRCd
        # styles will work (hopefully) using the regular wildhost parsing.
        v4cloak = re.match("^(?:[0-9]{1,3}\.){2}[a-z]{1,3}\.[a-z]{1,3}",
            hostname)
        if v4cloak:
            return True
        else:
            return False

    def _isv6IP(self, ipstr):    
        try:
            socket.inet_pton(socket.AF_INET6, ipstr)
            return True
        except socket.error:
            return False
        except AttributeError:
            # if inet_pton is not available, use our super-duper
            # lazy regexp instead!
            v6ip = re.match("([0-9a-fA-F]{1,4}:{1,2}){2,8}", ipstr)
            if v6ip:
                return True
            else:
                return False         
            
    def _isvHost(self, hostname):
        if "/" in hostname or hostname.endswith("."):
            return True
        return False
    
    def _isv6cloak(self, hostname):
        if ":" in hostname:
            # Look for unreal-style cloaks (1234abcd:2345bcde:3456cdef:IP)
            v6cloaku = re.match("([0-9A-F]{8}:){3}IP", hostname)
            # Use our super lazy regexp for charybdis-style v6 cloaks
            v6cloakc = re.match("([0-9a-z]{1,4}:{1,2}){2,8}", hostname)       
            if v6cloaku:
                return 'u'
            elif v6cloakc:
                return 'c'
        else: # doesn't even include a : , why bother checking?
            return False

    def banmask(self, irc, msg, args, nick):
        """[<nick>]
        Returns a nice banmask for <nick>. If <nick> is not given, returns a
         banmask for the person who called the command.
        """
        if not nick:
            nick = msg.nick
        unick, ident, host = self._SplitHostmask(irc, nick)
        bantype = self.registryValue('banType')
        if bantype == '1':
            banmask = '*!*@%s' % host
        elif bantype == '2':
            banmask = '*!%s@%s' % (ident, host)
        else:
            splithost = host.split('.', 2)
            v6splithost = host.split(":", 3)
            wildhost = ''
            if self.registryValue('smartBans'):
                if self._isv4IP(host) or \
                    self._isv4cloak(host):
                    v4cloak = host.split(".", 2)
                    wildhost = '%s.%s.*' % (v4cloak[0], v4cloak[1])
                elif self._isvHost(host):
                    wildhost = host
                elif self._isv6IP(host) or \
                    self._isv6cloak(host) == 'c':
                    try:
                        wildhost = '%s:%s:%s:*' % (v6splithost[0],
                            v6splithost[1], v6splithost[2])
                    except IndexError:
                        wildhost = host
                elif self._isv6cloak(host) == 'u':
                    try:
                        wildhost = '*:%s:%s:IP' % (v6splithost[1], 
                            v6splithost[2])
                    except IndexError:
                        wildhost = host
            if not wildhost:
                if len(splithost) <= 2:
                    wildhost = host # Hostmask is too short
                else:
                    wildhost = '*.%s.%s' % (splithost[1], splithost[2])
            if bantype == '3':
                banmask = '*!*@%s' % wildhost
            if bantype == '4':
                banmask = '*!%s@%s' % (ident, wildhost)
        irc.reply(banmask)
    banmask = wrap(banmask, [(additional('nick'))])
    
Class = Hostmasks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
