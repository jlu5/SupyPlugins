###
# Copyright (c) 2014, James Lu (GLolol)
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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NoTrigger')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class NoTrigger(callbacks.Plugin):
    """Mods outFilter to prevent the bot from triggering other bots."""
    
    def isChanStripColor(self, irc, channel):
        c = irc.state.channels[channel]
        if 'S' in c.modes or 'c' in c.modes:
            return True
        return False
    
    def outFilter(self, irc, msg):
        if msg.command == 'PRIVMSG' and \
            (self.registryValue('enable', msg.args[0]) or not \
            ircutils.isChannel(msg.args[0])):
            s = msg.args[1]
            prefixes = ["+", "$", ";", ".", "%", "!", "`", "\\", "@", "&", 
                        "*", "~", ":", "^", "(", ")", "-", "=", ">", "<",
                        # 003 = Colour, 002 = Bold, 017 = Reset Formatting, 
                        # 037 = Underline
                        ",", "\003", "\002", "\017", "\037"]
            # suffixes = ["moo"]
            rpairs = {"\007":"",
                     }
            if self.isChanStripColor(irc, msg.args[0]):
                rpairs['moo'] = 'm#oo'
            else:
                rpairs['moo'] = 'm\003oo'
            if self.registryValue('spaceBeforeNicks', msg.args[0]):
                # If the last character of the first word ends with a ',' or ':',
                # prepend a space.
                if s.split()[0][-1] in [",", ":"]:
                    s = " " + s
            # Handle actions properly but destroy any other \001 (CTCP) messages
            if s.startswith("\001") and not s.startswith("\001ACTION"):
                s = s[1:-1]
            for k, v in rpairs.iteritems():
                s = s.replace(k, v)
            for item in prefixes:
                if s.startswith(item):
                    s = " " + s
            msg = ircmsgs.privmsg(msg.args[0], s, msg=msg)
        return msg


Class = NoTrigger


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
