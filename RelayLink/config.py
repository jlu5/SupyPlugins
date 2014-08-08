###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2013-2014, James Lu (GLolol)
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
    _ = PluginInternationalization('RelayLink')
except:
    # This are useless functions that's allow to run the plugin on a bot
    # without the i18n plugin
    _ = lambda x:x
    internationalizeDocstring = lambda x:x

def configure(advanced):
    from supybot.questions import output, expect, anything, something, yn
    conf.registerPlugin('RelayLink', True)


class ColorNumber(registry.String):
    """Value must be a valid color number (01, 02, 03, 04, ..., 16)"""
    def set(self, s):
        if s not in ('01', '02', '03', '04', '05', '06', '07', '08', '09',
                     '10', '11', '12', '13', '14', '15', '16'):
            self.error()
            return
        self.setValue(s)
ColorNumber = internationalizeDocstring(ColorNumber)


RelayLink = conf.registerPlugin('RelayLink')
conf.registerChannelValue(RelayLink, 'color',
    registry.Boolean(True, _("""Determines whether the bot will color relayed
    PRIVMSGs so as to make the messages easier to read.""")))
conf.registerChannelValue(RelayLink, 'hostmasks',
    registry.Boolean(True, _("""Determines whether the bot will relay the
    hostmask of the person joining or parting the channel when he or she joins
    or parts.""")))
conf.registerChannelValue(RelayLink, 'noHighlight',
    registry.Boolean(False, _("""Determines whether the bot should prefix nicks
    with a hyphen (-) to prevent excess highlights (in PRIVMSGs and actions).""")))
conf.registerChannelValue(RelayLink, 'nicks',
    registry.Boolean(True, _("""Determines whether the bot will relay the
    nick of the person sending a message (you probably want this turned on).""")))
conf.registerChannelValue(RelayLink, 'includeNetwork',
    registry.Boolean(True, _("""Determines whether the bot will include the
    network in relayed PRIVMSGs; if you're only relaying between two networks,
    it's somewhat redundant, and you may wish to save the space.""")))

conf.registerGroup(RelayLink, 'remotepm')
conf.registerChannelValue(RelayLink.remotepm, 'enable',
    registry.Boolean(False, _("""Determines whether cross-network PMs through the
    bot will be allowed.""")))
conf.registerChannelValue(RelayLink.remotepm, 'useNotice',
    registry.Boolean(True, _("""Determines whether cross-network PMs should use notices
    instead of PRIVMSGs.""")))
conf.registerChannelValue(RelayLink.remotepm, 'useHostmasks',
    registry.Boolean(True, _("""Determines whether cross-network PMs should show hostnames
    instead of just the user's nick.""")))

conf.registerGroup(RelayLink, 'antiflood')
conf.registerGlobalValue(RelayLink.antiflood, 'enable',
    registry.Boolean(False, _("""Determines whether flood protection should
    be used by the relayer.""")))
conf.registerGlobalValue(RelayLink.antiflood, 'privmsgs',
    registry.NonNegativeInteger(0, _("""Determines how many PRIVMSGs the bot will allow
    before flood protection is triggered. This setting should be set based on how much
    traffic a channel gets, so a default is not included. Setting this' to 0
    effectively disables flood prevention.""")))
conf.registerGlobalValue(RelayLink.antiflood, 'nonPrivmsgs',
    registry.NonNegativeInteger(0, _("""Determines how many non-PRIVMSG
    events (joins, parts, nicks, etc.) the bot will allow before flood
    protection is triggered. This setting should be set based on how much
    traffic a channel gets, so a default is not included. Setting this to
    0 effectively disables flood prevention.""")))
conf.registerGlobalValue(RelayLink.antiflood, 'seconds',
    registry.PositiveInteger(30, _("""Determines how many seconds the bot
    should wait before relaying if flood prevention is triggered.""")))
conf.registerGlobalValue(RelayLink.antiflood, 'announce',
    registry.Boolean(True, _("""Determines whether the bot should announce
    flood alerts to the channel.""")))

class ValidNonPrivmsgsHandling(registry.OnlySomeStrings):
    validStrings = ('privmsg', 'notice', 'nothing')
conf.registerChannelValue(RelayLink, 'nonPrivmsgs',
    ValidNonPrivmsgsHandling('privmsg', _("""Determines whether the
    bot will use PRIVMSGs (privmsg), NOTICEs (notice), for non-PRIVMSG Relay
    messages (i.e., joins, parts, nicks, quits, modes, etc.), or whether it
    won't relay such messages (nothing)""")))

conf.registerGlobalValue(RelayLink, 'relays',
    registry.String('', _("""You shouldn't edit this configuration variable
    yourself unless you know what you do. Use 'relaylink {add|remove}' instead.""")))

conf.registerGlobalValue(RelayLink, 'substitutes',
    registry.String('', _("""You shouldn't edit this configuration variable
    yourself unless you know what you do. Use 'relaylink (no)substitute' instead.""")))

conf.registerGlobalValue(RelayLink, 'logFailedChanges',
    registry.Boolean(False, _("""Determines whether the bot should log failed config changes.""")))

conf.registerGroup(RelayLink, 'addall')
conf.registerGlobalValue(RelayLink.addall, 'max',
    registry.NonNegativeInteger(20, _("""Defines the maximum number of channels addall/removeall
    will try to process at once. Setting this below 1 will effectively disable the command.
    A value too high can freeze the bot, so be careful!""")))

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
