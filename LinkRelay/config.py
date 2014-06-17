###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2013, GLolol
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

import supybot.conf as conf
import supybot.ircutils as ircutils
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    from supybot.i18n import internationalizeDocstring
    _ = PluginInternationalization('LinkRelay')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def configure(advanced):
    from supybot.questions import output, expect, anything, something, yn
    conf.registerPlugin('LinkRelay', True)


class ColorNumber(registry.String):
    """Value must be a valid color number (01, 02, 03, 04, ..., 16)"""
    def set(self, s):
        if s not in ('01', '02', '03', '04', '05', '06', '07', '08', '09',
                     '10', '11', '12', '13', '14', '15', '16'):
            self.error()
            return
        self.setValue(s)
ColorNumber = internationalizeDocstring(ColorNumber)


LinkRelay = conf.registerPlugin('LinkRelay')
conf.registerChannelValue(LinkRelay, 'color',
    registry.Boolean(False, _("""Determines whether the bot will color Relayed
    PRIVMSGs so as to make the messages easier to read.""")))
# This is a leftover entry and isn't implemented yet; taking this out so it 
# doesn't confuse any users -GLolol
# conf.registerChannelValue(LinkRelay, 'topicSync',
    # registry.Boolean(True, _("""Determines whether the bot will synchronize
    # topics between networks in the channels it Relays.""")))
conf.registerChannelValue(LinkRelay, 'hostmasks',
    registry.Boolean(False, _("""Determines whether the bot will Relay the
    hostmask of the person joining or parting the channel when he or she joins
    or parts.""")))
conf.registerChannelValue(LinkRelay, 'nicks',
    registry.Boolean(True, _("""Determines whether the bot will relay the
    nick of the person sending a message (you probably want this turned on).""")))
conf.registerChannelValue(LinkRelay, 'includeNetwork',
    registry.Boolean(True, _("""Determines whether the bot will include the
    network in Relayed PRIVMSGs; if you're only Relaying between two networks,
    it's somewhat redundant, and you may wish to save the space.""")))

conf.registerGroup(LinkRelay, 'nickstoIgnore')
conf.registerChannelValue(LinkRelay.nickstoIgnore, 'nicks',
    registry.SpaceSeparatedListOfStrings('', _("""Determines a list of nicks for the bot to
    ignore (takes a space-seperated list).""")))
conf.registerChannelValue(LinkRelay.nickstoIgnore, 'affectPrivmsgs',
    registry.Boolean(True, _("""Determines whether the bot will ignore PRIVMSGs
    from the nicks listed in nicksToIgnore. If set to False, the bot will only
    ignore joins/parts/nicks/modes/quits from those nicks.""")))

conf.registerGroup(LinkRelay, 'sepTags')
conf.registerChannelValue(LinkRelay.sepTags, 'channels',
    registry.String('@', _("""Determines the separator string used for the
    bot for channels (when both nicks and IncludeNetwork are on).""")))
conf.registerChannelValue(LinkRelay.sepTags, 'nicks',
    registry.String('/', _("""Determines the separator string used for the
    bot for nicks (when both nicks and IncludeNetwork are on).""")))
    
class ValidNonPrivmsgsHandling(registry.OnlySomeStrings):
    validStrings = ('privmsg', 'notice', 'nothing')
conf.registerChannelValue(LinkRelay, 'nonPrivmsgs',
    ValidNonPrivmsgsHandling('privmsg', _("""Determines whether the
    bot will use PRIVMSGs (privmsg), NOTICEs (notice), for non-PRIVMSG Relay
    messages (i.e., joins, parts, nicks, quits, modes, etc.), or whether it
    won't relay such messages (nothing)""")))

conf.registerGlobalValue(LinkRelay, 'relays',
    registry.String('', _("""You shouldn't edit this configuration variable
    yourself unless you know what you do. Use @LinkRelay {add|remove} instead.""")))

conf.registerGlobalValue(LinkRelay, 'substitutes',
    registry.String('', _("""You shouldn't edit this configuration variable
    yourself unless you know what you do. Use @LinkRelay (no)substitute instead.""")))

conf.registerGlobalValue(LinkRelay, 'logFailedChanges',
    registry.Boolean(False, _("""Determines whether the bot should log failed config changes.""")))

conf.registerGroup(LinkRelay, 'colors')
for name, color in {'info': '02',
                    'truncated': '14',
                    'mode': '06',
                    'join': '03',
                    'part': '12',
                    'kick': '04',
                    'nick': '10',
                    'quit': '07'}.items():
    conf.registerChannelValue(LinkRelay.colors, name,
        ColorNumber(color, _("""Color used for relaying %s messages.""") % name))
        
conf.registerGroup(LinkRelay, 'addall')
conf.registerGlobalValue(LinkRelay.addall, 'max',
    registry.NonNegativeInteger(20, _("""Defines the maximum number of channels addall/removeall
    will try to process at once. Setting this below 1 will effectively disable the command.
    A value too high can freeze the bot, so be careful!""")))

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
