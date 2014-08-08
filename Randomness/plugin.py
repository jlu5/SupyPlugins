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

#  ________  ________   __  ____  ____________  ______  ____________
# /_  __/ / / / ____/  / / / / / /_  __/  _/  |/  /   |/_  __/ ____/
#  / / / /_/ / __/    / / / / /   / /  / // /|_/ / /| | / / / __/
# / / / __  / /___   / /_/ / /___/ / _/ // /  / / ___ |/ / / /___
#/_/ /_/ /_/_____/   \____/_____/_/ /___/_/  /_/_/  |_/_/ /_____/
#  __________  ____  __    __       _____ __________  ________  ______
# /_  __/ __ \/ __ \/ /   / /      / ___// ____/ __ \/  _/ __ \/_  __/
#  / / / /_/ / / / / /   / /       \__ \/ /   / /_/ // // /_/ / / /
# / / / _, _/ /_/ / /___/ /___    ___/ / /___/ _, _// // ____/ / /   ??
#/_/ /_/ |_|\____/_____/_____/   /____/\____/_/ |_/___/_/     /_/
#
# Use at your own risk!
##
# But seriously though, this is supposed to be a joke, please don't be offended!

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks
import random
from base64 import b64decode
from supybot.utils.structures import TimeoutQueue
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Randomness')
except ImportError:
    _ = lambda x:x

class Randomness(callbacks.Plugin):
    """Add the help for "@plugin help Randomness" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(Randomness, self)
        self.__parent.__init__(irc)
        self.dotCounter = TimeoutQueue(10)
    ##
    # SHHHHHHHHHHH DON'T SPOIL THE JOKES DOWN HERE
    ##
    # OR I WILL BE VERY MAD AND FIND YOU
    ##
    # *insert ridiculous amount of code here*
    ##
    # ..why are you still here? >_>
    ##
    def doPrivmsg(self, irc, msg):
        if self.registryValue("enable"):
            dots = "." * random.randint(0,10) # added emphasis...............
            volatile = ["kicks ", "stabs ", "fites ", "bans ", "ddas ", "packets ", "beats "]
            exclaim = (("!" * random.randint(1,5)) + ("1" * random.randint(0,2))) * \
                random.randint(1,2) + ("!" * random.randint(-1,5))
            gemotes = ["xD", "=']", "\\o/", ":"+"3"*random.randint(1,4), "^_^"]
            bemotes = ["-_-", ":|", ":\\"]
            if irc.network.lower() == "overdrive-irc":
                if "wow" in irc.state.channels[msg.args[0]].ops and \
                    ircutils.stripFormatting(msg.args[1].lower()).startswith("wow"):
                    wowResponses1 = ["what is it",
                                    "hi %s%s" % (msg.nick, dots),
                                    "o/",
                                    "HI %s%s" % (msg.nick.upper(), dots),
                                    "go away "+random.choice(bemotes),
                                    "FFS"+random.choice(bemotes),
                                    "ffs i'm trying to work",
                                    "WHAT DO YOU WANT",
                                    "leave me alone "+random.choice(bemotes),
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
                    n = random.randint(-5, 101)
                    if n >= 42:
                        irc.queueMsg(ircmsgs.privmsg("BotServ", "say {} {}".format(msg.args[0],random.choice(wowResponses1))))
                    elif n >= 21:
                        irc.queueMsg(ircmsgs.privmsg("BotServ", "act {} {}".format(msg.args[0],random.choice(volatile)+msg.nick)))
                elif msg.nick.lower().startswith("brend"):
                    bad = ["chink", "nigr", "nigger", "chinq"] # Seriously though, racism *sucks*.
                    for w in bad:
                        if w in ircutils.stripFormatting(msg.args[1].lower()):
                            irc.queueMsg(ircmsgs.kick(msg.args[0], msg.nick, "RACIST"))
                        return
                    alsobad = ["veggie tales", 'whore', 'wh0re']
                    for w in alsobad:
                        if w in ircutils.stripFormatting(msg.args[1].lower()):
                            irc.queueMsg(ircmsgs.kick(msg.args[0], msg.nick, "nothx"))
                elif ircutils.stripFormatting(msg.args[1]) == ".":
                    dotresponses = ["r u mad?", "lol r u mad", "mmm dots", ",", "no spam pls" + dots, ":D", "ok"]
                    if len(self.dotCounter) >= 2:
                        r = random.random()
                        if r >= 0.5:
                            irc.queueMsg(ircmsgs.privmsg(msg.args[0], random.choice(dotresponses)))
                    else: self.dotCounter.enqueue([0])
                elif ircutils.stripFormatting(msg.args[1]) == "ok":
                    okresponses = ["not ok", "ok", "ko", "not ok"+unichr(2122), "no spam", "^why does everyone say that ._."]
                    r = random.randint(1, 23)
                    if r >= 17:
                        irc.queueMsg(ircmsgs.action(msg.args[0], random.choice(volatile)+msg.nick))
                    elif r >= 6:
                        irc.queueMsg(ircmsgs.privmsg(msg.args[0], random.choice(okresponses)))
            if irc.network.lower() in ["overdrive-irc", "stripechat"] and \
                b64decode('aGl0bGVyIGJsb3Nzb20=') in ircutils.stripFormatting(msg.args[1].lower()):
                irc.queueMsg(ircmsgs.privmsg(msg.args[0], msg.nick + ": the entire topic changes" + exclaim))
            if irc.network.lower() == "stripechat":
                r = random.random()
                if msg.args[1].lower().startswith("&topic") and "hackinbot" in msg.args[1].lower() \
                    and r >= 0.3:
                    irc.queueMsg(ircmsgs.privmsg(msg.args[0], "OH, hackinbot! " + random.choice(gemotes)))

Class = Randomness


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
