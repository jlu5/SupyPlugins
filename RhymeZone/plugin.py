# -*- coding: utf-8 -*-
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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('RhymeZone')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError("Beautiful Soup 4 is required for this plugin: "
                      "http://www.crummy.com/software/BeautifulSoup/bs4/"
                      "doc/#installing-beautiful-soup")

class RhymeZone(callbacks.Plugin):
    """Fetches rhymes from http://rhymezone.com/."""
    threaded = True

    @wrap(['text'])
    def rhymes(self, irc, msg, args, word):
        """<word/phrase>

        Looks up rhymes for the word/phrase given on rhymezone.com.
        """
        url = 'http://www.rhymezone.com/r/rhyme.cgi?typeofrhyme=perfect&%s' % utils.web.urlencode({'Word': word})
        data = utils.web.getUrl(url)
        soup = BeautifulSoup(data)

        results = []

        try:
            for tag in soup.find("div", {"id": "snippets_top"}).next_siblings:
                if tag.name == 'a':  # It's a rhyme result!
                    # Get rid of non-breaking spaces in IRC output
                    result = tag.text.replace('\xa0', ' ').strip()

                    # Each page ends with a bunch of links, such as one to a
                    # "words ending with xyz" page. Once we get here, there are no
                    # results left, and we can break.
                    if result.startswith('words ending with'):
                         break

                    results.append(result)

                elif tag.name == 'center':  # These are usually used for headings

                    # Get the heading text, cut at the first newline
                    text = tag.text.split('\n')[0]

                    # The dagger is used for a footnote about near-rhymes and how
                    # they work; we don't need this.
                    text = text.replace(' †', '').strip()

                    if text:  # Ignore empty content
                        # Add the results for this type to replies
                        results.append(ircutils.bold(text))

        except AttributeError:
            irc.error("Word or phrase not found.")

        else:
            # Join, tweak the formatting, and reply
            s = ', '.join(results)
            s = s.replace(':\x02,', ':\x02')
            s = s.replace(':\x02 \x02', ':\x02 (none), \x02')
            irc.reply(s)

Class = RhymeZone


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
