###
# Copyright (c) 2015-2020 James Lu <james@overdrivenetworks.com>
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
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('RelayNext')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('RelayNext', True)


RelayNext = conf.registerPlugin('RelayNext')

conf.registerChannelValue(RelayNext, 'color',
    registry.Boolean(True, _("""Determines whether the bot will color relayed
    PRIVMSGs so as to make the messages easier to read.""")))
conf.registerChannelValue(RelayNext, 'hostmasks',
    registry.Boolean(True, _("""Determines whether the bot will relay the
    hostmask of the person joining or parting the channel when he or she joins
    or parts.""")))
conf.registerChannelValue(RelayNext, 'noHighlight',
    registry.Boolean(False, _("""Determines whether the bot should prefix nicks
    with a hyphen (-) to prevent excess highlights (in PRIVMSGs and actions).""")))
conf.registerChannelValue(RelayNext, 'showPrefixes',
    registry.Boolean(False, _("""Determines whether the bot should status prefixes
    (@, %, +) when relaying.""")))
conf.registerChannelValue(RelayNext, 'ignoreRegexp',
    registry.Regexp(None, _("""If configured, text, part, and quit messages matching this regexp
                            will not be relayed. This may be useful for spam blocking.""")))

conf.registerGroup(RelayNext, 'antiflood')
conf.registerChannelValue(RelayNext.antiflood, 'enable',
    registry.Boolean(False, _("""Determines whether flood prevention should be enabled
    for the given channel.""")))
conf.registerChannelValue(RelayNext.antiflood, 'seconds',
    registry.PositiveInteger(20, _("""Determines how many seconds messages should be queued
        for flood protection.""")))
conf.registerChannelValue(RelayNext.antiflood, 'maximum',
    registry.PositiveInteger(15, _("""Determines the maximum amount of incoming messages
        the bot will allow from a relay channel before flood protection is triggered.""")))
conf.registerChannelValue(RelayNext.antiflood.maximum, 'nonPrivmsgs',
    registry.PositiveInteger(10, _("""Determines the maximum amount of incoming non-PRIVMSG events
        the bot will allow from a relay channel before flood protection is triggered.""")))
conf.registerChannelValue(RelayNext.antiflood, 'timeout',
    registry.PositiveInteger(60, _("""Determines the amount of time in seconds the bot should
        block messages if flood protection is triggered.""")))

conf.registerGroup(RelayNext, 'events')

_events = {'quit': True, 'join': True, 'part': True,
           'nick': True, 'mode': True, 'kick': True,
           'topic': False}
for ev in _events:
    conf.registerChannelValue(RelayNext.events, 'relay%ss' % ev,
        registry.Boolean(_events[ev], """Determines whether the bot should relay %ss.""" % ev))
conf.registerChannelValue(RelayNext.events, 'userIgnored',
    registry.SpaceSeparatedListOfStrings(['PRIVMSG', 'MODE'], ("""Determines what events
        the relay should ignore from ignored users. Ignores are added using
        Limnoria's global ignore system.""")))
conf.registerChannelValue(RelayNext.events, 'relaySelfMessages',
    registry.Boolean(True, ("""Determines whether the bot should relay its own messages.
        You may wish to disable this if you are running plugins that announce to the same channel
        on multiple networks (e.g. RSS).""")))
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
