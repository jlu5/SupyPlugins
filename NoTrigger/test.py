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

from supybot.test import *


class NoTriggerTestCase(ChannelPluginTestCase):
    plugins = ('NoTrigger', 'Utilities', 'Reply')
    config = {'supybot.plugins.notrigger.enable': True,
              'supybot.plugins.notrigger.spaceBeforeNicks': True,
              'supybot.plugins.notrigger.blockCtcp': True}

    def testSpaceBeforePrefixes(self):
        self.assertNotRegexp('echo !test', '^!test$')

    def testSpaceBeforeNicks(self):
        self.assertNotRegexp('echo example: hello', '^example: hello$')
        self.assertNotRegexp('echo user1, hello', '^user1, hello$')

    def testCTCPBlocking(self):
        self.assertResponse('echo \x01PING abcd\x01', 'PING abcd')
        self.assertAction('reply action jumps around', 'jumps around')

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
