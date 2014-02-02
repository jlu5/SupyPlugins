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
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Isup')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class Isup(callbacks.Plugin):
    """Add the help for "@plugin help Isup" here
    This should describe *how* to use this plugin."""
    
    def _getreply(self, url):
        data = utils.web.getUrl("http://isup.me/%s" % url)
        if "It's just you." in data:
            # irc.reply("It's just you. %s is up." % url)
            try:
                return self.registryValue("replies.up") % url
            except TypeError:
                return self.registryValue("replies.up")
        elif "looks down from here" in data: 
            try:
                return self.registryValue("replies.down") % url
            except TypeError:
                return self.registryValue("replies.down")
        elif "doesn't look like a site" in data:
            try:
                return self.registryValue("replies.unknown") % url
            except TypeError:
                return self.registryValue("replies.unknown")
        else: 
            return "An error occurred, please check your URL and try again."      
    
    def check(self, irc, msg, args, url): 
        """<url>
        Check if a website is up or down using isup.me."""
        try: 
            url = url.split("://")[1]
        except: 
            pass
        irc.reply(self._getreply(url))   
    check = wrap(check, (['something']))

Class = Isup

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
