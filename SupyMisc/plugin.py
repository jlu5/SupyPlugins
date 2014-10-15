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
import random
import itertools

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.world as world
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('SupyMisc')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class SupyMisc(callbacks.Plugin):
    """This plugin provides commands and basic interfaces that aren't
    available in stock Supybot (e.g. access to Python's random.uniform(),
    etc.)"""
    threaded = True

    ### Some semi-useful utilities
    def scramble(self, irc, msg, args, text):
        """<text>
        An alternative to Supybot's Filter scramble command, but without keeping the first and last letters of each word. """
        L = []
        for word in text.split():
            word = list(word)
            random.shuffle(word)
            word = ''.join(word)
            L.append(word)
        irc.reply(' '.join(L))
    scramble = wrap(scramble, ['text'])
    
    def repeat(self, irc, msg, args, num, text):
        """<num> <text>
        Returns <text> repeated <num> times. <num> must be a positive integer. 
        To keep leading and trailing spaces, it is recommended to quote the <text>
        argument " like this ". """
        maxN = self.registryValue("repeat.max")
        if num <= maxN:
            irc.reply(text * num)
        else:
            irc.error("The <num> value given is too large. Current "
                "maximum: {}".format(maxN), Raise=True)
    repeat = wrap(repeat, ['positiveInt', 'text'])
    
    def uniform(self, irc, msg, args, a, b):
        """<a> <b>
        Return a random floating point number N such that a <= N <= b for a <= b and b <= N 
        <= a for b < a. A frontend to Python's random.uniform() command."""
        irc.reply(random.uniform(a,b))
    uniform = wrap(uniform, ['float', 'float'])

    def randrange(self, irc, msg, args, start, stop, step):
        """<start> <stop> [<step>]
        Returns a random integer between <start> and <stop>, with optional [<step>]
        between them."""
        if not step: step = 1
        irc.reply(random.randrange(start, stop, step))
    randrange = wrap(randrange, ['int', 'int', additional('int')])

    def mreplace(self, irc, msg, args, bad, good, text):
        """<bad substring1>,[<bad substring2>],... <good substring1,[<good substring2>],...> <text>

        Replaces all instances of <bad substringX> with <good substringX> in <text> (from left to right).
        Essentially an alternative for Supybot's format.translate, but with support for substrings
        of different lengths."""
        if len(good) != len(bad):
            irc.error("<bad substrings> must be the same length as <good substrings>", Raise=True)
        for pair in itertools.izip(bad, good):
            text = text.replace(pair[0], pair[1])
        irc.reply(text)
    mreplace = wrap(mreplace, [commalist('something'), commalist('something'), 'text'])

## Fill this in later, try to prevent forkbombs and stuff.
#    def permutations(self, irc, msg, args, length, text):
#        """[<length>] <text>
#
#        Returns [<length>]-length permutations of <text>. If not specified, [<length>]
#        defaults to the length of <text>."""
#        s = ' '.join(''.join(p) for p in itertools.permutations(text, length or None))
#        irc.reply(s)
#    permutations = wrap(permutations, [additional('int'), 'text'])

    ### Generic informational commands (ident fetcher, channel counter, etc.)

    def serverlist(self, irc, msg, args):
        """A command similar to the !networks command, but showing configured servers instead 
        of the connected one."""
        L = []
        for ircd in world.ircs:
            # fetch a list of tuples in the format (server, port)
            for server in conf.supybot.networks.get(ircd.network).servers():
                # list every server configured for every network connected
                L.append("%s: %s" % (ircd.network, server[0]))
        irc.reply(', '.join(L)) # finally, join them up in a comma-separated list
    serverlist = wrap(serverlist)

    def netcount(self, irc, msg, args):
        """takes no arguments.
        Counts the amount of networks the bot is on. """
        irc.reply(len(world.ircs))
    netcount = wrap(netcount)
    
    def supyplugins(self, irc, msg, args):
        """takes no arguments.
        Returns a URL for the source of this plugin. """
        irc.reply("SupyPlugins source is available at: https://github.com/GLolol/SupyPlugins")
    supyplugins = wrap(supyplugins)

    def chancount(self, irc, msg, args):
        """takes no arguments.
        Counts the amount of channels the bot is on. """
        irc.reply(len(irc.state.channels.keys()))
    chancount = wrap(chancount)

    def getchan(self, irc, msg, args):
        """takes no arguments.
        Returns the name of the current channel. """
        channel = msg.args[0]
        if ircutils.isChannel(channel):
             irc.reply(channel)
        else:
             irc.reply(None)
    getchan = wrap(getchan)
        
    def me(self, irc, msg, args):
        """takes no arguments.
        Returns the nick of the person who called the command.
        """
        irc.reply(msg.nick)
    me = wrap(me)

    def botnick(self, irc, msg, args):
        """takes no arguments.
        Returns the nick of the bot.
        """
        irc.reply(irc.nick)
    botnick = wrap(botnick)

    def getident(self, irc, msg, args, nick):
        """[<nick>]
        Returns the ident of <nick>. If <nick> is not given, returns the host
        of the person who called the command.
        """
        if not nick:
            nick = msg.nick
        irc.reply(ircutils.userFromHostmask(irc.state.nickToHostmask(nick)))
    getident = wrap(getident, [(additional('nick'))])

    def gethost(self, irc, msg, args, nick):
        """[<nick>]
        Returns the host of <nick>. If <nick> is not given, return the host
        of the person who called the command.
        """
        if not nick:
            nick = msg.nick
        irc.reply(ircutils.hostFromHostmask(irc.state.nickToHostmask(nick)))
    gethost = wrap(gethost, [(additional('nick'))])

Class = SupyMisc

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
