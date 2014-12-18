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
import re
import json
try:
    from itertools import izip
except ImportError:
    izip = zip

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
        maxN = self.registryValue("maxLen")
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
        if stop <= start:
            irc.error("<stop> must be larger than <start>.", Raise=True)
        irc.reply(random.randrange(start, stop, step))
    randrange = wrap(randrange, ['int', 'int', additional('positiveInt')])

    def mreplace(self, irc, msg, args, bad, good, text):
        """<bad substring1>,[<bad substring2>],... <good substring1,[<good substring2>],...> <text>

        Replaces all instances of <bad substringX> with <good substringX> in <text> (from left to right).
        Essentially an alternative for Supybot's format.translate, but with support for substrings
        of different lengths."""
        maxLen = self.registryValue("maxLen")
        lbad, lgood = len(good), len(bad)
        if lbad > maxLen or lgood > maxLen:
            irc.error("Too many substrings given. Current maximum: {}" \
                .format(maxN), Raise=True)
        if lbad != lgood:
            irc.error("<bad substrings> must be the same length as <good substrings>", Raise=True)
        for pair in izip(bad, good):
            text = text.replace(pair[0], pair[1])
        irc.reply(text)
    mreplace = wrap(mreplace, [commalist('something'), commalist('something'), 'text'])

    def colors(self, irc, msg, args):
        """takes no arguments.

        Replies with a display of IRC colour codes."""
        s = ("\x03,00  \x0F\x0300 00\x0F \x03,01  \x0F\x0301 01\x0F \x03,02  \x0F\x0302 02\x0F \x03,03  "
             "\x0F\x0303 03\x0F \x03,04  \x0F\x0304 04\x0F \x03,05  \x0F\x0305 05\x0F \x03,06  \x0F\x0306"
             " 06\x0F \x03,07  \x0F\x0307 07\x0F \x03,08  \x0F\x0308 08\x0F \x03,09  \x0F\x0309 09\x0F "
             "\x03,10  \x0F\x0310 10\x0F \x03,11  \x0F\x0311 11\x0F \x03,12  \x0F\x0312 12\x0F \x03,13  "
             "\x0F\x0313 13\x0F \x03,14  \x0F\x0314 14\x0F \x03,15  \x0F\x0315 15\x0F")
        irc.reply(s)
    colors = wrap(colors)
    colours = wrap(colors)

    def tld(self, irc, msg, args, text):
        """<tld>

        Checks whether <tld> is a valid TLD using IANA's TLD database
        (http://www.iana.org/domains/root/db/)."""
        db = "http://www.iana.org/domains/root/db/"
        text = text.split(".")[-1] # IANA's DB doesn't care about second level domains
        # Encode everything in IDN in order to support international TLDs
        try: # Python 2
            s = text.decode("utf8").encode("idna")
        except AttributeError: # Python 3
            s = text.encode("idna").decode()
        try:
            data = utils.web.getUrl(db + s)
        except utils.web.Error as e:
            if "HTTP Error 404:" in str(e):
                irc.error("No results found for TLD .{}".format(text), Raise=True)
            else:
                irc.error("An error occurred while contacting IANA's "
                    "TLD Database.", Raise=True)
        else:
            irc.reply(".{} appears to be a valid TLD, see {}{}".format(text, db, s))
    tld = wrap(tld, ['something'])

    ### Generic informational commands (ident fetcher, channel counter, etc.)
    def serverlist(self, irc, msg, args):
        """takes no arguments.
        A command similar to the 'networks' command, but showing configured servers
        instead of the connected one."""
        L, res = {}, []
        for ircd in world.ircs:
            net = ircd.network
            # Get a list of server:port strings for every network, and put this
            # into a dictionary (netname -> list of servers)
            L[net] = (':'.join(str(x) for x in s) for s in \
                conf.supybot.networks.get(net).servers())
        for k, v in L.items():
            # Check SSL status and format response
            sslstatus = "\x0303on\x03" if conf.supybot.networks.get(k).ssl() else \
                "\x0304off\x03"
            res.append("\x02%s\x02 (%s) [SSL: %s]" % (k, ', '.join(v), sslstatus))
        irc.reply(', '.join(res))
    serverlist = wrap(serverlist)

    def netcount(self, irc, msg, args):
        """takes no arguments.
        Counts the amount of networks the bot is on. """
        irc.reply(len(world.ircs))
    netcount = wrap(netcount)
    
    def supyplugins(self, irc, msg, args, text):
        """[<file/folder>]
        Returns a URL for the source of this repository. If <file/folder>
        is specified, it will expand a link to it, if such file or folder
        exists."""
        base = 'https://github.com/GLolol/SupyPlugins'
        if not text:
            irc.reply(format("SupyPlugins source is available at: %u", base))
            return
        apiurl = 'https://api.github.com/repos/GLolol/SupyPlugins/contents/'
        text = re.sub("\/+", "/", text)
        try:
            text, line = text.split("#")
        except ValueError:
            line = ''
        try:
            fd = utils.web.getUrl(apiurl + text)
            data = json.loads(fd.decode("utf-8"))
            if type(data) == list:
                s = "%s/tree/master/%s" % (base, text)
            else:
                s = data['html_url']
        except (AttributeError, utils.web.Error):
            irc.error('Not found.', Raise=True)
        if line:
            s += "#%s" % line
        irc.reply(format('%u', s))
    supyplugins = wrap(supyplugins, [additional('text')])

    def chancount(self, irc, msg, args):
        """takes no arguments.
        Counts the amount of channels the bot is on. """
        irc.reply(len(irc.state.channels))
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
