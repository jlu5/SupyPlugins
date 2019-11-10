###
# Copyright (c) 2019, James Lu <james@overdrivenetworks.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA.
###

from supybot import conf, registry, utils
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Qalculate')
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
    conf.registerPlugin('Qalculate', True)


Qalculate = conf.registerPlugin('Qalculate')
conf.registerGlobalValue(Qalculate, 'command',
    registry.String(utils.findBinaryInPath('qalc') or '',
        _("""Set the path of the 'qalc' command. On snap installations this is "qalculate.qalc".""")))
conf.registerGlobalValue(Qalculate, 'timeout',
    registry.PositiveInteger(2000, _("""Set the timeout for the qalc command in milliseconds.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
