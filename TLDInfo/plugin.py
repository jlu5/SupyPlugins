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
    _ = PluginInternationalization('TLDInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class TLDInfo(callbacks.Plugin):
    """Fetches TLD information from IANA's database (http://www.iana.org/domains/root/db/)."""
    threaded = True

    def tld(self, irc, msg, args, text):
        """<tld>

        Checks whether <tld> is a valid TLD using IANA's database
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
                irc.reply("No results found for TLD {} (using "
                    "http://www.iana.org/domains/root/db)".format("."+text))
            else:
                irc.error("An error occurred while contacting IANA's "
                    "TLD Database.", Raise=True)
        else:
            irc.reply("{} appears to be a valid TLD, see {}".format(("."+text), (db+s)))
    tld = wrap(tld, ['something'])


Class = TLDInfo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
