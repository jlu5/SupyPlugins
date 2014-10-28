###
# Copyright (c) 2014, James Lu
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

import json
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Voteserv')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class Voteserv(callbacks.Plugin):
    """Small plugin for storing and manipulating votes/polls."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Voteserv, self)
        self.__parent.__init__(irc)
        self.vfilename = conf.supybot.directories.data.dirize("votes.db")
        try:
            with open(self.vfilename, "r") as f:
                self.votedb = json.load(f)
        except IOError:
            self.log.debug("Voteserv: failed to load votes database %s"
                ", creating a new one..." % self.vfilename)
            self.votedb = {}
        except ValueError:
            self.log.warning("Voteserv: Invalid JSON found in votes database "
                "%s, replacing it with a new one!" % self.vfilename)

    def loadVoteDB(self):
        self.log.debug("Voteserv: loading votes database "+self.vfilename)
        with open(self.vfilename, "r") as f:
            self.votedb = json.load(f)
            
    def exportVoteDB(self):
        self.log.debug("Voteserv: exporting votes database "+self.vfilename)
        with open(self.vfilename, 'w') as f:
            json.dump(self.votedb, f, indent=4, separators=(',', ': '))
            f.write("\n")
            
    def die(self):
        self.__parent.die()
        try:
            self.exportVoteDB()
        except IOError as e:
            self.log.error("Failed to export votes database: " + str(e))
            
    def _lazyhostmask(self, host):
        return "*!"+host.split("!",1)[1]
        
    def _formatAction(self, action):
        a = action.split()
        try: n = self.votedb[action][0]
        except KeyError: n = 0
        if len(a) >= 2:
            return "\x02%s\x02 %s. (Votes: \x02%s\x02)" % \
                (a[0], ' '.join(a[1:]), n)
        return "\x02%s\x02. (Votes: \x02%s\x02)" % \
            (action, n)

    def vote(self, irc, msg, args, action):
        """<something>

        Votes for something. It doesn't actually perform any actions directly,
        but could be an interesting way to get user feedback."""
        action = action.lower()
        try:
            if self._lazyhostmask(msg.prefix) in self.votedb[action]:
                irc.error("You have already voted to %s." % action, Raise=True)
        except KeyError:
            self.votedb[action] = [0]
        self.votedb[action][0] += 1
        irc.reply("%s voted to %s" % (msg.nick,self._formatAction(action)))
        self.votedb[action].append(self._lazyhostmask(msg.prefix))
    vote = wrap(vote, ['text'])

    def voteexport(self, irc, msg, args):
        """takes no arguments.
        
        Exports votes stored in memory to file: data/votes.db
        This is also done automatically when the plugin is unloaded or 
        reloaded."""
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
        self.votedb = {}
        irc.replySuccess()
    voteclear = wrap(voteclear, ['admin'])

    def votes(self, irc, msg, args, action):
        """<action>
        
        Returns the amount of people that have voted for <action>."""
        try:
            n = self.votedb[action.lower()][0]
        except KeyError:
            n = 0
        if irc.nested:
            irc.reply(n)
        else:
            irc.reply('\x02%s\x02 %s voted to %s' % 
            (n, 'person has' if n == 1 else 'people have',
            self._formatAction(action)))
    votes = wrap(votes, ['text'])

    def cheat(self, irc, msg, args, num, action):
        """<number of votes> <action>
        
        Sets the number of votes for <action> to a certain amount,
        perfect for rigged elections!
        This will also reset the list of hosts that have voted for
        <action>, allowing everyone to vote again."""
        self.votedb[action.lower()] = [num]
        irc.replySuccess()
    cheat = wrap(cheat, ['admin', 'int', 'text'])

Class = Voteserv


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
