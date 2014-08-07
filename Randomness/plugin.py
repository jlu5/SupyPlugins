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
import supybot.ircmsgs as ircmsgs
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks
import random
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Randomness')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class Randomness(callbacks.Plugin):
    """Add the help for "@plugin help Randomness" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def doPrivmsg(self, irc, msg):
        if self.registryValue("enable") and \
            irc.network.lower() == "overdrive-irc" and \
            "wow" in irc.state.channels[msg.args[0]].ops and \
            ircutils.stripFormatting(msg.args[1].lower()).startswith("wow"):
            dots = "." * random.randint(0,10) # added emphasis...............
            wowResponses1 = ["what is it",
                            "hi %s%s" % (msg.nick, dots),
                            "o/",
                            "HI %s%s" % (msg.nick.upper(), dots),
                            "go away -_-",
                            "FFS",
                            "ffs i'm trying to work",
                            "WHAT DO YOU WANT",
                            "leave me alone :|",
                            "ugh",
                            "pls",
                            "stop" + dots,
                            "stop it!",
                            "reproted to fbi for harrassment" + dots,
                            "-_-",
                            msg.nick + " pls",
                            "i cry",
                            "fml",
                            "?",
                            ".",
                            "/join 0",
                            "/part SCREW U GUYS IM LEAVING AND NEVER COMING "
                                "BACK AGAIN!! IT'S ALL %s'S FAULT I FKN HATE "
                                "YOU ALL \x02</3" % msg.nick.upper(),
                            "stop highlighting me!",
                            "\x02%s\x02 added to ignore list." % msg.nick,
                            "!votekline " + msg.nick]
            wowResponses2 = ["kicks ", "stabs ", "fites ", "bans "]
            brenden = ["stfu blossom", "stfu brenda", "~~brenda blossom~~"]
            n = random.randint(-5, 101)
            #if n >= 96 and msg.nick.lower().startswith("brend"):
            #    irc.queueMsg(ircmsgs.privmsg("BotServ", "say {} {}".format(msg.args[0],random.choice(brenden))))
            if n >= 42:
                irc.queueMsg(ircmsgs.privmsg("BotServ", "say {} {}".format(msg.args[0],random.choice(wowResponses1))))
            elif n >= 21:
                irc.queueMsg(ircmsgs.privmsg("BotServ", "act {} {}".format(msg.args[0],random.choice(wowResponses2)+msg.nick)))


Class = Randomness


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
