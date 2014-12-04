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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import random
import json
try: # Python 3
    from urllib.parse import urlencode
except ImportError: # Python 2
    from urllib import urlencode
    from string import printable
from sys import version_info

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('WTE')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class WTE(callbacks.Plugin):
    """Worst Translations Ever! plugin. Translates text through 
    multiple rounds of Google Translate to get amazing results!"""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(WTE, self)
        self.__parent.__init__(irc)
        if version_info[0] < 3:
            self.log.warning("WTE: Due to Unicode handling issues, "
                "Unicode characters will be stripped from this plugin's "
                "input/output. For optimal results, please upgrade the "
                "bot to Python 3.")
        self.langs = ('sw', 'sv', 'is', 'et', 'te', 'tr', 'mr', 'nl', 'sl', 
        'id', 'gu', 'hi', 'az', 'hmn', 'ko', 'da', 'bg', 'lo', 'so', 'tl', 
        'hu', 'ca', 'cy', 'bs', 'ka', 'vi', 'eu', 'ms', 'fr', 'no', 'hy', 
        'ro', 'ru', 'th', 'it', 'ta', 'sq', 'ceb', 'bn', 'de', 'zh-CN', 
        'be', 'lt', 'ne', 'fi', 'pa', 'iw', 'km', 'mt', 'ht', 'mi', 'lv', 
        'jw', 'sr', 'ar', 'ig', 'ha', 'pt', 'ga', 'af', 'zu', 'la', 'el', 
        'cs', 'uk', 'ja', 'hr', 'kn', 'gl', 'mk', 'fa', 'sk', 'mn', 'es', 
        'ur', 'pl', 'eo', 'yo', 'en', 'yi')

    def getTranslation(self, irc, sourceLang, targetLang, text):
        args = {"client": "p", "sl":sourceLang, "tl":targetLang}
        if version_info[0] < 3:
            # Python 2's Unicode handling is just horrible. I've tried a
            # dozen different combinations of encoding and decoding and they
            # all fail with a stupid, useless UnicodeDecodeError. We're
            # just going to strip all non-ASCII characters until
            # this stupid issue gets fixed. -GLolol
            args['q'] = filter(lambda x: x in printable, text)
        else:
            args['q'] = text
        url = "http://translate.google.com/translate_a/t?"+ \
            urlencode(args)
        try:
            data = json.loads(utils.web.getUrl(url).decode("utf-8"))
        except utils.web.Error as e:
            irc.error(str(e), Raise=True)
        if "dict" in data:
            return data["dict"][0]["entry"][0]["word"]
        else:
            return data["sentences"][0]["trans"]

    def wte(self, irc, msg, args, text):
        """wte <text>
        
        Worst Translations Ever! plugin. Translates <text> through
        multiple rounds of Google Translate to get amazing results!
        """
        outlang = self.registryValue('language', msg.args[0])
        if outlang not in self.langs:
            irc.error("Unrecognized output language. Please set "
                "'config plugins.wte.language' correctly.", Raise=True)
        ll = random.sample(self.langs, random.randint(6,12))
        for targetlang in ll:
            text = self.getTranslation(irc, "auto", targetlang, text)
        text = self.getTranslation(irc, "auto", outlang, text)
        text = text.strip()
        if not text:
            s = ("Error encoding/decoding response. If you are using "
                "Python 2, it is recommended to upgrade to "
                "Python 3 to suppress these kinds of errors, as there "
                "are some lingering issues handling Unicode on "
                "versions of Python 2.")
            irc.error(s, Raise=True)
        irc.reply(text)
    wte = wrap(wte, ['text'])

Class = WTE

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
