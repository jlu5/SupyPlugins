###
# Copyright (c) 2017, James Lu <james@overdrivenetworks.com>
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
import supybot.conf as conf
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Restart')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

import atexit
import os
import sys
import time

class Restart(callbacks.Plugin):
    """Restart plugin: provides a command to restart Limnoria from IRC."""

    @staticmethod
    def restart_atexit_hook():
        # Replace the currently running Supybot process with another one with the same
        # args.
        os.execl(sys.executable, os.path.basename(sys.executable), *sys.argv)

    @wrap(['owner', additional('text')])
    def restart(self, irc, msg, args, text):
        """[<text>]

        Restarts the bot with the QUIT message <text>. If <text> is not given,
        the default quit message (supybot.plugins.Owner.quitMsg) will be used.
        If there is no default quitMsg set, your nick will be used. The standard
        substitutions ($version, $nick, etc.) are all handled appropriately.
        """
        if conf.daemonized:  # XXX fix this
            irc.error("Not supported on daemonized instances.", Raise=True)

        atexit.register(self.restart_atexit_hook)
        self.log.info('Restart: Attempting to restart Limnoria.')
        # Reuse the 'quit' command of the Owner plugin.
        irc.getCallback('Owner').quit(irc, msg, [text or ''])

Class = Restart


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
