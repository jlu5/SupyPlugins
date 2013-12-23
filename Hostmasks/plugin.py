###
# Copyright (c) 2013, GLolol (GLolol1@hotmail.com)
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
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Hostmasks')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class Hostmasks(callbacks.Plugin):
    """Add the help for "@plugin help Hostmasks" here
    This should describe *how* to use this plugin."""
    pass
    
    def _SplitHostmask(self, irc, nick):
        # Split the hostmask of someone into 3 sections: nick, ident, and host
        try: 
            splithostmask = re.split('[!@]', irc.state.nickToHostmask(nick))
        except KeyError:
            irc.error('There is no such nick \'%s\'%s.' % nick, Raise=True)
        if len(splithostmask) != 3:
            self.log.warning('Hostmasks: Invalid hostmask length received' 
                ' for %s on %s. This should not be happening!'
                % (nick, irc.network))
            irc.error('Invalid hostmask length received! (this should not '
                'be happening!)', Raise=True)
        return splithostmask
    
    def gethost(self, irc, msg, args, nick):
        """[<nick>]
        Returns the host of <nick>. If <nick> is not given, returns the host
        of the person who called the command.
        """
        if not nick:
            nick = msg.nick
        irc.reply(self._SplitHostmask(irc, nick)[2])
    gethost = wrap(gethost, [(additional('nick'))])
    
    def getident(self, irc, msg, args, nick):
        """[<nick>]
        Returns the ident of <nick>. If <nick> is not given, returns the host
        of the person who called the command.
        """
        if not nick:
            nick = msg.nick
        irc.reply(self._SplitHostmask(irc, nick)[1])
    getident = wrap(getident, [(additional('nick'))])
    
    def me(self, irc, msg, args):
        """takes no arguments.
        Returns the nick of the person who called the command.
        """
        irc.reply(msg.nick)
    me = wrap(me)  
    
    def banmask(self, irc, msg, args, nick):
        """[<nick>]
        Returns a nice banmask for <nick>. If <nick> is not given, returns a
         banmask for the person who called the command.
        """
        if not nick:
            nick = msg.nick
        splithostmask = self._SplitHostmask(irc, nick)
        bantype = self.registryValue('banType')
        # Set banmask per bantype: 1 = *!*@blahip.myisp.net;
        # 2 = *!~ident@blahip.myisp.net; 3 = *!*@*.myisp.net;
        # 4 = *!~ident@*.myisp.net
        if bantype == 1:
            banmask = '%s%s' % ('*!*@', splithostmask[2])
        if bantype == 2:
            banmask = '%s%s%s%s' % ('*!', splithostmask[1], '@', 
                splithostmask[2])
        else:
            # Split the host too so you can ban things like *!*@*.isp.net
            splithost = re.split(r"\.", splithostmask[2])
            # Attempt to detect 
            if len(splithost) <= 2: # or re.search("/", splithostmask[2]):
                wildhost = splithostmask[2]
            else:
                wildhost = '%s%s%s%s' % ('*.', splithost[-2], '.', 
                    splithost[-1])
            if bantype == 3:
                banmask = '%s%s' % ('*!*@', wildhost) 
            if bantype == 4:
                banmask = '%s%s%s%s' % ('*!', splithostmask[1], '@', wildhost)
        irc.reply(banmask)
    banmask = wrap(banmask, [(additional('nick'))])
    
Class = Hostmasks


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
