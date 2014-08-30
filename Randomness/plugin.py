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
# But seriously though, the references in this script are mostly mere jokes,
# please don't be offended if you see anything strange.

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircmsgs as ircmsgs
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks
import supybot.conf as conf
import random
import json
import re
from time import sleep
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
        self.vfilename = conf.supybot.directories.data.dirize(irc.network+".votes")
        try:
            with open(self.vfilename, "r") as f:
                self.votes = json.load(f)
        except IOError:
            self.votes = {}

    def loadVoteDB(self):
        with open(self.vfilename, "r") as f:
            self.votes = json.load(f)
            
    def exportVoteDB(self):
        with open(self.vfilename, 'w') as f:
            json.dump(self.votes, f)
            f.write("\n")
            
    def die(self):
        self.__parent.die()
        try:
            self.exportVoteDB()
        except IOError as e:
            self.log.error("Failed to export Votes DB: " + str(e))

    # The code below contains automatic replies then turned on. Since this
    # is a mostly personal plugin, they will only activate on certain
    # predefined networks.
    def _attack(self, target):
        bde = "%sasE%s4"%('B','6')
        throws = ['poorly written code', 'knives', 
            "Te"+"chman", 'various objects',
            "Techm"+"ango", 'grenades',
            "j4j"+"ackj", 'netsplits']
        spells = ['fire', 'ice', 'death', '\x02DEATH\x02', 
            'poison', 'stupid']
        attacks = throws + spells + ['bricks', 'knives', 
            "idiots from #freenode", "her army of trolls",
            "her ~~godly~~ oper powers",
            'confusingly bad english', 
            "gbyers' immaturity",
            "YnJlbmRpIGhpdGxlciBibG9zc29t".decode(bde)]
        n = random.random()
        if n >= 0.82:
            return 'casts %s at %s'%(random.choice(spells), target)
        elif n >= 0.76:
            return 'drops the bass on %s'%target
        elif n >= 0.72:
            return 'fites %s'%target
        elif n >= 0.48:
            return 'attacks %s with %s'%(target, random.choice(attacks))
        else:
            return 'throws %s at %s'%(random.choice(throws),target)

    def doPrivmsg(self, irc, msg):
        if ircutils.isChannel(msg.args[0]) and self.registryValue("enable", msg.args[0]):
            dots = "." * random.randint(0,10) # added emphasis...............
            ow = "ow"+("w"*random.randint(0,4))
            volatile = ("kicks ", "stabs ", "fites ", "bans ", "ddas ", "packets ", "beats ")
            exclaim = (("!" * random.randint(1,5)) + ("1" * random.randint(0,2))) * \
                random.randint(1,2) + ("!" * random.randint(-1,5))
            gemotes = ["xD", "=']", "\\o/", ":"+"3"*random.randint(1,4), "^_^"]
            meh = (";/", ":\\", ":/")
            bemotes = meh + (":(", ":|", '-_-')
            semotes = (":<", ";_;", ";-;", "D:", ">:", "x(")
            if irc.network.lower() == "overdrive-irc":
                # if msg.nick.lower() == 'gbyers' and msg.args[1].lower() == 'hi lily':
                    # irc.queueMsg(ircmsgs.kick(msg.args[0], msg.nick, "stfu"))
                if "fishbot" in irc.state.channels[msg.args[0]].users:
                    hurtresponses = [ow, ";_;", ow+" :(", "RIP", "i cry",
                        "ouch", "what was that for "+random.choice(semotes),
                        "!voteban "+msg.nick, "PLS", "rood", "owowowowow", 
                        "omg "+random.choice(semotes), 
                        "bots have feelings too!", "wtf", "watch it!"]
                    if re.match(r"^\x01ACTION ((attacks|stabs) {n} with |"
                        r"(drops|throws|casts|thwacks) (.*? (at|on|with) "
                        r"{n}|{n} (at|on|with) .*?)|fites {n}).*?\x01$".\
                        format(n=irc.nick), msg.args[1].lower(), re.I):
                        sleep(0.4)
                        n = random.random()
                        if n >= 0.45:
                            irc.queueMsg(ircmsgs.action(msg.args[0], self._attack(msg.nick)))
                        else:
                            irc.queueMsg(ircmsgs.privmsg(msg.args[0], random.choice(hurtresponses)))
                if "wow" in irc.state.channels[msg.args[0]].ops and \
                    ircutils.stripFormatting(msg.args[1].lower()).startswith("wow"):
                    wowResponses1 = ["what is it",
                                    "hi %s%s" % (msg.nick, dots),
                                    "o/",
                                    "HI %s%s" % (msg.nick.upper(), dots),
                                    "go away "+random.choice(bemotes),
                                    "FFS "+random.choice(bemotes),
                                    "ffs i'm trying to work",
                                    "WHAT DO YOU WANT",
                                    "leave me alone "+random.choice(bemotes),
                                    "hello, you've reached 'wow'. "
                                        "If you actually need to talk to me, "
                                        "press 1. if not, PISS OFF!",
                                    "stop highlighting me" + dots,
                                    "reproted to fbi for harassment" + dots,
                                    "-_-",
                                    msg.nick + " pls",
                                    "need something?",
                                    "r u mad",
                                    "ur made",
                                    "fml",
                                    "?",
                                    ".",
                                    "meh "+random.choice(meh),
                                    "/join 0",
                                    "/part SCREW U GUYS IM LEAVING AND NEVER COMING "
                                        "BACK AGAIN!! IT'S ALL %s'S FAULT I FKN HATE "
                                        "YOU ALL \x02</3" % msg.nick.upper(),
                                    "stop highlighting me!",
                                    "\x02%s\x02 added to ignore list." % msg.nick,
                                    "!votekline " + msg.nick]
                    n = random.randint(0, 91)
                    if n >= 60:
                        irc.queueMsg(ircmsgs.privmsg("BotServ", "say {} {}".format(msg.args[0],random.choice(wowResponses1))))
                    elif n >= 50:
                        irc.queueMsg(ircmsgs.privmsg("BotServ", "act {} {}".format(msg.args[0],random.choice(volatile)+msg.nick)))
#                elif msg.nick.lower().startswith("brend"):
#                    bad = ["chink", "nigr", "nigger", "chinq"] # Seriously though, racism *sucks*.
#                    for w in bad:
#                        if w in ircutils.stripFormatting(msg.args[1].lower()):
#                            irc.queueMsg(ircmsgs.kick(msg.args[0], msg.nick, "RACIST"))
#                        return
#                    alsobad = ["veggie tales", 'whore', 'wh0re']
#                    for w in alsobad:
#                        if w in ircutils.stripFormatting(msg.args[1].lower()):
#                            irc.queueMsg(ircmsgs.kick(msg.args[0], msg.nick, "nothx"))
                if ircutils.stripFormatting(msg.args[1]) == ".":
                    dotresponses = ["r u mad?", "lol r u mad", "mmm dots", ",", "no spam pls" + dots, ":D", "ok"]
                    if len(self.dotCounter) >= 2:
                        r = random.random()
                        if r >= 0.5:
                            irc.queueMsg(ircmsgs.privmsg(msg.args[0], random.choice(dotresponses)))
                    else: self.dotCounter.enqueue([0])
                elif ircutils.stripFormatting(msg.args[1]) == "ok":
                    okresponses = ["not ok", "ok", "ko",
                        "okay*", "O.K.", "^why does everyone say that ._.",
                        "\x01ACTION ok's %s\x01" % msg.nick,
                        "no", "Objection! \x02Not\x02 okay!", "meh "+random.choice(meh),
                        "yeah ok w/e man.", "\x01ACTION sighs\x01",
                        "you're pretty ok.", "hmph", "I AGREE WITH YOU, "+msg.nick+dots]
                    r = random.randint(1, 23)
                    if r >= 19:
                        irc.queueMsg(ircmsgs.action(msg.args[0], random.choice(volatile)+msg.nick))
                    elif r >= 7:
                        irc.queueMsg(ircmsgs.privmsg(msg.args[0], random.choice(okresponses)))
            if irc.network.lower() in ("overdrive-irc", "stripechat") and \
                ('aXRsZXIgYmxvc3NvbQ==').decode('base'+'64') in ircutils.stripFormatting(msg.args[1].lower()):
                irc.queueMsg(ircmsgs.privmsg(msg.args[0], msg.nick + ": the entire topic changes" + exclaim))
 #           if irc.network.lower() == "stripechat":
 #               r = random.random()
 #               if msg.args[1].lower().startswith("&topic") and "hackinbot" in msg.args[1].lower() \
 #                   and r >= 0.3:
 #                   irc.queueMsg(ircmsgs.privmsg(msg.args[0], "OH, hackinbot! " + random.choice(gemotes)))

    def _lazyhostmask(self, host):
        return "*!"+host.split("!",1)[1]

    def vote(self, irc, msg, args, action):
        """<thing>

        Votes for something. It doesn't actually perform any actions directly,
        but could be an interesting way to get user feedback."""
        try:
            if self._lazyhostmask(msg.prefix) in self.votes[action][1]:
                irc.reply("You have already voted to %s." % action)
                return
        except KeyError:
            self.votes[action] = [0, []]
        self.votes[action][0] += 1
        try:
            a, b = action.split(" ",1)
        except ValueError:
            irc.error("Not enough arguments.", Raise=True)
        irc.reply("%s voted to \x02%s\x02 %s. (Votes: \x02%s\x02)" % (msg.nick, a, b, self.votes[action][0]))
        self.votes[action][1].append(self._lazyhostmask(msg.prefix))
    vote = wrap(vote, ['text'])
    
    def voteexport(self, irc, msg, args):
        """takes no arguments.
        
        Exports votes stored in memory to file: data/%s(network).votes
        This is done automatically when the plugin is unloaded or reloaded."""
        try:
            self.exportVoteDB()
        except IOError as e:
            irc.error("IOError caught exporting DB: "+str(e))
        else:
            irc.replySuccess()
    voteexport = wrap(voteexport, ['admin'])

    def voteimport(self, irc, msg, args):
        """takes no arguments.
        
        Imports the vote database for the current network."""
        try:
            self.loadVoteDB()
        except IOError as e:
            irc.error("IOError caught importing DB: "+str(e))
        else:
            irc.replySuccess()
    voteimport = wrap(voteimport, ['admin'])
    
    def voteclear(self, irc, msg, args):
        """takes no arguments.
        
        Clears all votes stored in memory. Use with caution!"""
        self.votes = {}
        irc.replySuccess()
    voteclear = wrap(voteclear, ['admin'])

Class = Randomness


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
