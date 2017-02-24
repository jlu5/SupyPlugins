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
    raise ImportError('This plugin requires Python 3!')

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('TranslateParty')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class TranslateParty(callbacks.Plugin):
    """Translates text through multiple rounds of Google Translate to get amusing results!"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(TranslateParty, self)
        self.__parent.__init__(irc)
        self.langs = {
            'af': 'Afrikaans',
            'sq': 'Albanian',
            'ar': 'Arabic',
            'hy': 'Armenian',
            'az': 'Azerbaijani',
            'eu': 'Basque',
            'be': 'Belarusian',
            'bn': 'Bengali',
            'bs': 'Bosnian',
            'bg': 'Bulgarian',
            'ca': 'Catalan',
            'ceb': 'Cebuano',
            'ny': 'Chichewa',
            'zh-CN': 'Chinese Simplified',
            'zh-TW': 'Chinese Traditional',
            'hr': 'Croatian',
            'cs': 'Czech',
            'da': 'Danish',
            'nl': 'Dutch',
            'en': 'English',
            'eo': 'Esperanto',
            'et': 'Estonian',
            'tl': 'Filipino',
            'fi': 'Finnish',
            'fr': 'French',
            'gl': 'Galician',
            'ka': 'Georgian',
            'de': 'German',
            'el': 'Greek',
            'gu': 'Gujarati',
            'ht': 'Haitian Creole',
            'ha': 'Hausa',
            'iw': 'Hebrew',
            'hi': 'Hindi',
            'hmn': 'Hmong',
            'hu': 'Hungarian',
            'is': 'Icelandic',
            'ig': 'Igbo',
            'id': 'Indonesian',
            'ga': 'Irish',
            'it': 'Italian',
            'ja': 'Japanese',
            'jw': 'Javanese',
            'kn': 'Kannada',
            'kk': 'Kazakh',
            'km': 'Khmer',
            'ko': 'Korean',
            'lo': 'Lao',
            'la': 'Latin',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'mk': 'Macedonian',
            'mg': 'Malagasy',
            'ms': 'Malay',
            'ml': 'Malayalam',
            'mt': 'Maltese',
            'mi': 'Maori',
            'mr': 'Marathi',
            'mn': 'Mongolian',
            'my': 'Myanmar (Burmese)',
            'ne': 'Nepali',
            'no': 'Norwegian',
            'fa': 'Persian',
            'pl': 'Polish',
            'pt': 'Portuguese',
            'ma': 'Punjabi',
            'ro': 'Romanian',
            'ru': 'Russian',
            'sr': 'Serbian',
            'st': 'Sesotho',
            'si': 'Sinhala',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'so': 'Somali',
            'es': 'Spanish',
            'su': 'Sudanese',
            'sw': 'Swahili',
            'sv': 'Swedish',
            'tg': 'Tajik',
            'ta': 'Tamil',
            'te': 'Telugu',
            'th': 'Thai',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'ur': 'Urdu',
            'uz': 'Uzbek',
            'vi': 'Vietnamese',
            'cy': 'Welsh',
            'yi': 'Yiddish',
            'yo': 'Yoruba',
            'zu': 'Zulu',
        }

    def _jsonRepair(self, data):
        while ',,' in data:
            data = data.replace(',,', ',null,')
        while '[,' in data:
            data = data.replace('[,', '[')
        return data

    def getTranslation(self, irc, sourceLang, targetLang, text):
        """
        Fetches translations from Google Translate, given the source language,
        target language, and text.
        """
        args = {"sl": sourceLang, "tl": targetLang, 'q': text}
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&"+ \
            urlencode(args)
        self.log.debug("TranslateParty: Using URL %s", url)
        headers = {'User-Agent': ('Mozilla/5.0 (X11; Linux i586; rv:31.0) '
                                 'Gecko/20100101 Firefox/31.0')}
        try:
            data = utils.web.getUrlFd(url, headers).read().decode("utf-8")
        except utils.web.Error as e:
            self.log.exception("TranslateParty: getTranslation errored (probably malformed or too long text)")
            return text
        data = self._jsonRepair(data)
        data = json.loads(data)
        return ''.join(x[0] for x in data[0])

    @wrap(['text'])
    def tp(self, irc, msg, args, text):
        """tp <text>

        Translates <text> through multiple rounds of Google Translate to get amusing results.
        """
        outlang = self.registryValue('language', msg.args[0])
        if outlang not in self.langs:
            irc.error("Unrecognized output language. Please set "
                "'config plugins.wte.language' correctly.", Raise=True)

        # Randomly choose 4 to 8 languages from the list of supported languages.
        # The amount can be adjusted if you really wish - 4 to 8 is reasonable
        # in that it gives interesting results but doesn't spam Google's API
        # (and risk getting blocked) too much.
        ll = random.sample(self.langs.keys(), random.randint(4,8))
        self.log.debug(format("TranslateParty: Using %i languages: %L "
            "(outlang %s)", len(ll), ll, outlang))

        # For every language in this list, translate the text given from
        # auto-detect into the target language, and replace the original text
        # with it.
        for targetlang in ll:
            text = self.getTranslation(irc, "auto", targetlang, text)
        text = self.getTranslation(irc, "auto", outlang, text)
        text = ircutils.stripFormatting(text)
        text = text.strip()

        if self.registryValue("verbose", msg.args[0]):
            # Verbose output was requested, show the language codes AND
            # names that we translated through.
            languages = [ircutils.bold("%s [%s]" % (self.langs[lang], lang)) for lang in ll]
            irc.reply(format("Translated through \x02%i\x02 languages: %L "
                             "(output language %s)", len(ll), languages, outlang))
        irc.reply(text)

Class = TranslateParty

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
