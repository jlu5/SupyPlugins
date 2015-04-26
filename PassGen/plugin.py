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
import string
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PassGen')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class PassGen(callbacks.Plugin):
    """Generates passwords on the fly!"""
    threaded = True

    def mkpasswd(self, irc, msg, args, len):
        """[<len>]
        
        Makes a randomly generated password, [<len>] characters long if
        specified. Otherwise, uses the bot's configured default length.
        (see config plugins.PassGen.defaultLen)"""
        maxlen = self.registryValue('maxLength')
        if not len:
            len = self.registryValue('defaultLen')
        elif len > maxlen:
            irc.error("The specified length ({}) is longer than the maximum "
                "allowed on this bot. Current maximum: {}".format(len, maxlen), \
                Raise=True)
        rg = random.SystemRandom()
        letters = string.ascii_letters + string.digits + self.registryValue('symbols')
        pw = ''.join(rg.choice(letters) for n in range(len))
        irc.reply(pw, private=True)
    mkpasswd = wrap(mkpasswd, [(additional('positiveInt'))])

Class = PassGen

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
