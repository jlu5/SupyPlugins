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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('OperUp')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class OperUp(callbacks.Plugin):
    """Simple plugin that allows Supybot to oper up on configured networks, on
        connect and manually."""

    def do376(self, irc, msg):
        """Oper up on connect. This listens for numerics 376 (end of MOTD) and
        422 (MOTD not found)."""
        if not self.registryValue('autoOper'):
            return
        if irc.network in self.registryValue('operNets'):
            if self.registryValue("operName") and \
                self.registryValue("operPass"):
                irc.sendMsg(ircmsgs.IrcMsg(command="OPER",
                    args=[self.registryValue("operName"),
                    self.registryValue("operPass")]))
            else:
                self.log.warning("OperUp: Bot is set to oper on network %s, but"
                    " operName and/or operPass are not defined!", irc.network)

    do422 = do376

    def do381(self, irc, msg):
        self.log.info("OperUp: Received 381 (successfully opered up) from "
            "network %s.", irc.network)
        if self.registryValue("operModes"):
            self.log.info("OperUp: Opered up on %s, sending user modes %s",
                irc.network, ''.join(self.registryValue("operModes")))
            irc.sendMsg(ircmsgs.mode(irc.nick,
                self.registryValue("operModes")))

    def do385(self, irc, msg):
        self.log.info("OperUp: Received 385 (not opered anymore) from network"
            " %s.", irc.network)

    def do461(self, irc, msg):
        self.log.warning("OperUp: Received 461 (some command needs more "
            "parameters) from network %s.", irc.network)

    def do464(self, irc, msg):
        self.log.error("OperUp: Received 464 (password mismatch) from "
            "network %s.", irc.network)

    def do481(self, irc, msg):
        self.log.warning("OperUp: Received 481 (missing oper privileges) "
            "from network %s.", irc.network)

    def do491(self, irc, msg):
        self.log.error("OperUp: Received 491 (server has been configured "
            "to disallow the your bot's host from opering) from network %s.",
            irc.network)

    def operup(self, irc, msg, args):
        """takes no arguments.
        Makes the bot Oper up using the name and password defined in config.
        """
        if irc.nested:
            irc.error("This command cannot be nested.", Raise=True)
        if irc.network in self.registryValue('operNets'):
            if self.registryValue("operName") and \
                self.registryValue("operPass"):
                irc.sendMsg(ircmsgs.IrcMsg(command="OPER",
                    args=[self.registryValue("operName"),
                    self.registryValue("operPass")]))
                irc.replySuccess()
            else:
                irc.error(_("Either the operName or the operPass "
                    "configuration values were not properly defined. Please "
                    "check to see if these values are correct!"))
        else:
            irc.error(_("This network is not configured for opering! (see"
                " 'config plugins.OperUp.opernets')"))
    operup = wrap(operup, ['owner'])

    def deoper(self, irc, msg, args):
        """takes no arguments.
        Makes the bot deoper by setting user modes -Oo on itself.
        """
        if irc.nested:
            irc.error("This command cannot be nested.", Raise=True)
        irc.sendMsg(ircmsgs.mode(irc.nick, "-Oo"))
        irc.replySuccess()
    deoper = wrap(deoper, ['owner'])

Class = OperUp


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
