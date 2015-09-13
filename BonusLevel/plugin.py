###
# Copyright (c) 2015, James Lu
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

from bs4 import BeautifulSoup

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('BonusLevel')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class BonusLevel(callbacks.PluginRegexp):
    """Snarfer for various things on BonusLevel.org."""
    threaded = True
    # Need this to specify levelSnarfer() as a regexp listener!
    regexps = ("levelSnarfer", "packIDSnarfer")

    def _lvlid(self, irc, lvlid):
        url = 'http://www.bonuslevel.org/games/level_-_%s.html' % lvlid
        return self._fetch(irc, url)

    def _packid(self, irc, packid):
        url = 'http://www.bonuslevel.org/games/pack_-_%s.html' % packid
        return self._fetch(irc, url, itemname="Pack")

    def _fetch(self, irc, url, itemname="Level"):
        self.log.debug('BonusLevel: fetching URL %s', url)
        data = utils.web.getUrl(url)
        soup = BeautifulSoup(data)
        # BeautifulSoup here to parse; the HTML is invalid and makes etree complain :(
        div = soup.find("div", class_="ilbg").div
        linkobj = div.a
        if linkobj is None:
            irc.error("No such level/pack.", Raise=True)
        # Get rid of the relative link.
        gamelink = linkobj["href"].replace('..', 'http://www.bonuslevel.org')
        title = linkobj.find("span", class_="gtitle").text
        author = div.ul.find_all('li')[1].a.text.strip()
        s = format("%s %s by %s: %u", itemname, ircutils.bold(title), ircutils.bold(author), gamelink)
        irc.reply(s)

    def levelSnarfer(self, irc, msg, match):
        r"\[?lvlid\=(\d+)\]?"
        payload = match.group(1)
        if payload and self.registryValue("enable", msg.args[0]):
            self.log.info('BonusLevel: got level ID %s from levelSnarfer for %s', payload, msg.prefix)
            self._lvlid(irc, payload)

    def packIDSnarfer(self, irc, msg, match):
        r"\[?packid\=(\d+)\]?"
        payload = match.group(1)
        if payload and self.registryValue("enable", msg.args[0]):
            self.log.info('BonusLevel: got level ID %s from packIDSnarfer for %s', payload, msg.prefix)
            self._packid(irc, payload)

    @wrap(['positiveInt'])
    def level(self, irc, msg, args, lvlid):
        """<level id>

        Finds and returns the game+link for <level id>, if it exists."""
        self._lvlid(irc, lvlid)

    @wrap(['positiveInt'])
    def pack(self, irc, msg, args, packid):
        """<pack id>

        Finds and returns the game+link for <pack id>, if it exists."""
        self._packid(irc, packid)


Class = BonusLevel


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
