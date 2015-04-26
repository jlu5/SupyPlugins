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
import random
import os.path
from sys import version_info

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Namegen')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Namegen(callbacks.Plugin):
    """Simple random name generator."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Namegen, self)
        self.__parent.__init__(irc)
        self.names = {}
        for fn in ('starts', 'middles', 'ends'):
            with open(os.path.join(os.path.dirname(__file__), '%s.txt') % fn) \
                    as f:
                self.names[fn] = f.read().splitlines()

    def _namegen(self, syl):
        """Generates a random name."""
        numSyl = random.randint(0, syl)
        starts = random.choice(self.names['starts'])
        middles = ''.join(random.sample(self.names['middles'], numSyl))
        ends = random.choice(self.names['ends'])
        name = "{}{}{}".format(starts, middles, ends)
        return name

    def namegen(self, irc, msg, args, count, syl):
        """[<count>] [<syllables>]

        Generates random names. If not specified, [<count>] defaults to 10.
        [<syllables>] specifies the maximum number of syllables a name can
        have, and defaults to the value set in 'config
        plugins.namegen.syllables'."""
        confsyl = self.registryValue("syllables")
        maxsyl = max(confsyl, 10)
        if not count:
            count = 10
        elif count > 100:
            irc.error("Too many names to count!", Raise=True)
        elif syl and syl > maxsyl:
            irc.error("Too many syllables specified.", Raise=True)
        syl = syl or confsyl
        r = range if version_info[0] >= 3 else xrange
        s = ', '.join([self._namegen(syl) for _ in r(count)])
        irc.reply(s)
    namegen = wrap(namegen, [optional('positiveInt'), optional('positiveInt')])


Class = Namegen


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
