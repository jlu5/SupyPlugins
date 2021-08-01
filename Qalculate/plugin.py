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

import subprocess

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Qalculate')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Qalculate(callbacks.Plugin):
    """Frontend for the Qalculate! desktop calculator"""

    @wrap([('checkCapability', 'trusted'), getopts({'update-exrates': ''}), 'text'])
    def calc(self, irc, msg, args, optlist, expression):
        """[--update-exrates] <expression>

        Calculates <expression> using Qalculate!. Exchange rate data will be automatically
        updated as needed.
        """
        cmd = self.registryValue('command')
        timeout = self.registryValue('timeout')

        if not cmd:
            irc.error(_("Please install the `qalc' program from Qalculate! or configure "
                        "plugins.Qalculate.command if it is installed to a different path."),
                      Raise=True)
        elif not expression:
            irc.error(_("No expression given."), Raise=True)

        if 'update-exrates' in dict(optlist):
            args = [cmd, '-exrates', '-time', str(timeout), expression]
        else:
            args = [cmd, '-time', str(timeout), expression]
        # As of writing all program communication is through stdout
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL)
        stdout_data, __ = proc.communicate()

        # Qalculate prompts before downloading exchange rate data from the Internet.
        # By closing STDIN we prevent all questions from being asked, since those might freeze
        # the program if the prompt is not recognized (e.g. due to translations).
        # The side effect is that this actually causes qalc to crash, so the workaround here
        # is to update exchange rate data manually.
        if b'Do you wish to update the exchange rates now?' in stdout_data:
            irc.error(_("Exchange rate data is out of date: please retry with --update-exrates"),
                      Raise=True)

        output = stdout_data.decode('utf-8').splitlines()
        irc.replies(output, oneToOne=False)

Class = Qalculate


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
