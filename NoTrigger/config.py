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

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NoTrigger')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('NoTrigger', True)


NoTrigger = conf.registerPlugin('NoTrigger')
conf.registerChannelValue(NoTrigger, 'enable',
    registry.Boolean(True, _("""Enable protection against triggering other bots.""")))
conf.registerChannelValue(NoTrigger, 'spaceBeforeNicks',
    registry.Boolean(False, _("""Add a space before messages beginning with 
        "blah: " or "blah, ", preventing the bot from triggering other bots that
        respond to nick. This can cause some weird spacings with error messages and
        other command replies, so I wouldn't recommend enabling it unless absolutely
        necessary.""")))
conf.registerChannelValue(NoTrigger, 'colorAware',
    registry.Boolean(True, _("""Toggles whether the bot should be aware of colour-stripping
        modes. (+c or +S on most IRCds)""")))
conf.registerGroup(NoTrigger, 'colorAware')
conf.registerChannelValue(NoTrigger.colorAware, 'modes',
    registry.SpaceSeparatedListOfStrings("c S", _("""Determines a list of modes that should
        be treated as colour-blocking modes. This is usually +c (block) and +S (stripcolour) on
        UnrealIRCd/InspIRCd, and just +c (stripcolour) on charybdis-based daemons.""")))
conf.registerChannelValue(NoTrigger, 'blockCtcp',
    registry.Boolean(False, _("""Determines whether the bot should block all CTCPs (\001 codes)
        except CTCP actions. If you are using the Ctcp plugin, you will want to turn this off.""")))


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
