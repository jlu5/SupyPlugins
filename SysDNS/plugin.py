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
import os
import subprocess

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('SysDNS')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x:x

class SysDNS(callbacks.Plugin):
    """An alternative to Supybot's built-in DNS function, using the 'host' DNS lookup
    utility available on the host machine.
    """
    threaded = True
    def dns(self, irc, msg, args, optlist, target, nameserver):
        """[--type type] <target host> [<name server>]
        Looks up a DNS hostname using the 'host' binary available on the system. --type
        controls the type of record to look for. (A, AAAA, etc.)
        """
        cmd = self.registryValue('command')

        if not cmd:
            irc.error('This plugin is not correctly configured. Please configure '
                      'supybot.plugins.SysDNS.command appropriately.', Raise=True)
        else:
            optlist = dict(optlist)
            recordtype = optlist.get('type')
            if recordtype:
                args = [cmd, '-t', dict(optlist)['type'], target]
            else:
                args = [cmd, target]

            if nameserver:
                args.append(nameserver)

            try:
                with open(os.devnull) as null:
                    inst = subprocess.Popen(args,
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE,
                                            stdin=null)
            except OSError as e:
                irc.error('It seems the configured \'host\' command was '
                          'not available (%s).' % e, Raise=True)
            result = inst.communicate()
            if result[1]: # stderr
                irc.error(' '.join(result[1].decode('utf8').split()))
            if result[0]: # stdout
                response = result[0].decode('utf8').splitlines()
                response = [l for l in response if l]
                irc.replies(response)
            elif not result[1]:
                # Only show this explicit error if stderr doesn't provide something more specific.
                # This case will trigger on domains that exist but have no A/AAAA/MX records.
                irc.error('This domain exists, but no records of type %s were found.'
                          % (recordtype or 'A/AAAA/MX'))

    dns = thread(wrap(dns, [getopts({'type':'something'}), 'somethingWithoutSpaces',
                            additional('somethingWithoutSpaces')]))


Class = SysDNS


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
