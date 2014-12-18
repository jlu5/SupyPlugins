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
import string
from sys import version_info

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

    def __init__(self, irc):
        self.__parent = super(NoTrigger, self)
        self.__parent.__init__(irc)
        # This uses Unicode Character 'ZERO WIDTH SPACE' (U+200B) for
        # padding, which looks nicer (it's invisible) and does the trick.
        if version_info[0] >= 3:
            self.padchar = "\u200B"
        else:
            from codecs import unicode_escape_decode as u
            self.padchar = u('\u200B')[0]

    def isChanStripColor(self, irc, channel):
        c = irc.state.channels[channel]
        for item in self.registryValue('colorAware.modes'):
            if item in c.modes:
                return True
        return False

    def outFilter(self, irc, msg):
        if msg.command == 'PRIVMSG' and \
            ircutils.isChannel(msg.args[0]) and \
            self.registryValue('enable', msg.args[0]):
            s = msg.args[1]
            prefixes = string.punctuation
            rpairs = {"\007":""
                     }
            suffixes = ("moo")
            if self.registryValue('colorAware') and \
                self.isChanStripColor(irc, msg.args[0]) and \
                s.startswith(("\003", "\002", "\017", "\037", "\026")):
                # \003 = Colour (Ctrl+K), \002 = Bold (Ctrl+B), \017 =
                # Reset Formatting (Ctrl+O), \037 = Underline,
                # \026 = Italic/Reverse video
                self.log.debug("NoTrigger (%s/%s): prepending message with "
                    "a space since our message begins with a formatting code "
                    "and the channel seems to be blocking colors.",
                    msg.args[0], irc.network)
                s = self.padchar + s
            elif self.registryValue('spaceBeforeNicks', msg.args[0]) and \
                s.split()[0].endswith((",", ":")):
                # If the last character of the first word ends with a ',' or
                # ':', prepend a space.
                s = self.padchar + s
                self.log.debug("NoTrigger (%s/%s): prepending message with "
                    "a space due to config plugins.notrigger."
                    "spaceBeforeNicks.", msg.args[0], irc.network)
            # Handle actions properly but destroy any other \001 (CTCP) messages
            if self.registryValue('blockCtcp', msg.args[0]) and \
                s.startswith("\001") and not s.startswith("\001ACTION"):
                s = s[1:-1]
                self.log.debug("NoTrigger (%s/%s): blocking non-ACTION "
                    "CTCP due to config plugins.notrigger.blockCtcp.",
                     msg.args[0], irc.network)
            for k, v in rpairs.items():
                s = s.replace(k, v)
            if s.startswith(tuple(prefixes)):
                s = self.padchar + s
            if s.endswith(suffixes):
                s += self.padchar
            msg = ircmsgs.privmsg(msg.args[0], s, msg=msg)
        return msg

Class = NoTrigger

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
