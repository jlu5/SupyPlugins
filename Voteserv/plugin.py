###
# Copyright (c) 2014-2015, James Lu
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
import supybot.ircdb as ircdb
import supybot.callbacks as callbacks
import supybot.world as world
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

    def _pluralize(self, n):
        """Returns 's' if <n> is not 1."""
        return 's' if n != 1 else ''

    def __init__(self, irc):
        self.__parent = super(Voteserv, self)
        self.__parent.__init__(irc)
        self.vfilename = conf.supybot.directories.data.dirize("votes.db")
        self.loadVoteDB()
        world.flushers.append(self.exportVoteDB)

    def loadVoteDB(self):
        self.log.debug("Voteserv: loading votes database from "+self.vfilename)
        try:
            with open(self.vfilename, "r") as f:
                self.votedb = json.load(f)
        except IOError:
            self.log.error("Voteserv: failed to load votes database %s"
                ", creating a new one in memory...", self.vfilename)
            self.votedb = {}
        except ValueError:
            self.log.error("Voteserv: Invalid JSON found in votes database "
                "%s, creating a new one in memory...", self.vfilename)
            self.votedb = {}

    def exportVoteDB(self):
        self.log.debug("Voteserv: exporting votes database to "+self.vfilename)
        with open(self.vfilename, 'w') as f:
            json.dump(self.votedb, f, indent=4, separators=(',', ': '))
            f.write("\n")

    def die(self):
        try:
            self.exportVoteDB()
        except IOError as e:
            self.log.error("Failed to export votes database: " + str(e))
        world.flushers.remove(self.exportVoteDB)
        self.__parent.die()

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
        action = ircutils.stripFormatting(action.lower()).strip()
        override = self.registryValue("allowAdminOverride") and \
            ircdb.checkCapability(msg.prefix, 'admin')
        if not action: # It must be just whitespace or formatting codes
            irc.error("You must specify a proper action!", Raise=True)
        try:
            votedhosts = map(self._lazyhostmask, self.votedb[action][1:])
            if self._lazyhostmask(msg.prefix) in votedhosts and not override:
                irc.error("You have already voted to %r." % action, Raise=True)
        except KeyError:
            self.votedb[action] = [0]
        self.votedb[action][0] += 1
        irc.reply("%s voted to %s" % (msg.nick,self._formatAction(action)))
        self.votedb[action].append(msg.prefix)
    vote = wrap(vote, ['text'])

    def voteclear(self, irc, msg, args):
        """takes no arguments.

        Clears all votes stored in memory. Use with caution!"""
        self.votedb = {}
        irc.replySuccess()
    voteclear = wrap(voteclear, ['admin'])

    def votes(self, irc, msg, args, opts, action):
        """[--hosts] [--number] <action>

        Returns the amount of people that have voted for <action>. If
        --hosts is given, also show the hosts that have voted for <action>.
        If --number is given, only returns the number of people who has
        voted for <action> (useful for nested commands)."""
        action = ircutils.stripFormatting(action.lower()).strip()
        if not action:
            irc.error("You must specify a proper action!", Raise=True)
        try:
            n, hosts = self.votedb[action][0], self.votedb[action][1:]
        except KeyError:
            n, hosts = 0, None
        opts = dict(opts)
        if 'number' in opts:
            irc.reply(n)
        else:
            s = '\x02%s\x02 %s voted to %s' % \
                (n, 'person has' if n == 1 else 'people have', \
                self._formatAction(action))
            if 'hosts' in opts and n:
                s += format(" [%L]", list(set(hosts)))
            irc.reply(s)
    votes = wrap(votes, [getopts({'hosts':'', 'number':''}), 'text'])

    def cheat(self, irc, msg, args, num, action):
        """<number of votes> <action>

        Sets the number of votes for <action> to a certain amount,
        perfect for rigged elections!
        This will also reset the list of hosts that have voted for
        <action>, allowing everyone to vote again."""
        if not self.registryValue("allowCheat"):
            irc.error("This command is disabled; please set config plugins."
                "voteserv.allowCheat accordingly.", Raise=True)
        action = ircutils.stripFormatting(action.lower()).strip()
        if not action:
            irc.error("You must specify a proper action!", Raise=True)
        self.votedb[action] = [num]
        irc.replySuccess()
    cheat = wrap(cheat, ['admin', 'int', 'text'])

    def listallvotes(self, irc, msg, args):
        """<takes no arguments>.

        Returns the list of things that have been voted for, along
        with the number of votes for each."""
        items = self.votedb.items()
        if items:
            s = "; ".join(['"%s": \x02%s\x02 vote%s' % (k, v[0], self._pluralize(v[0]))
                for k, v in items])
            irc.reply(s)
        else:
            irc.error("The vote database is empty!")
    listallvotes = wrap(listallvotes)

Class = Voteserv


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
