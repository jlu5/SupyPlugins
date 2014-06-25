###
# Copyright (c) 2010, quantumlemur
# Copyright (c) 2011, Valentin Lorentz
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

from supybot.test import *

class TelayLinkTestCase(ChannelPluginTestCase):
    plugins = ('RelayLink','Config', 'User')

    def testAdd(self):
        self.assertNotError('config supybot.plugins.relaylink.relays ""')
        self.assertNotError('relaylink add --from #foo@bar --to #baz@bam')
        self.assertResponse('config supybot.plugins.relaylink.relays',
                            '#foo | bar | #baz | bam | ')

        self.assertNotError('config supybot.plugins.relaylink.relays ""')
        self.assertNotError('relaylink add --from #foo@bar --to #baz@bam '
                            '--reciprocal')
        self.assertResponse('config supybot.plugins.relaylink.relays',
                            '#foo | bar | #baz | bam |  || '
                            '#baz | bam | #foo | bar | ')

        self.assertNotError('config supybot.plugins.relaylink.relays ""')
        self.assertNotError('relaylink add --from #foo@bar')
        self.assertResponse('config supybot.plugins.relaylink.relays',
                            '#foo | bar | #test | test | ')

        self.assertNotError('config supybot.plugins.relaylink.relays ""')
        self.assertNotError('relaylink add --to #foo@bar')
        self.assertResponse('config supybot.plugins.relaylink.relays',
                            '#test | test | #foo | bar | ')

    def testRemove(self):
        self.assertNotError('config supybot.plugins.relaylink.relays '
                            '"#foo | bar | #baz | bam | "')
        self.assertNotError('relaylink remove --from #foo@bar --to #baz@bam')
        self.assertResponse('config supybot.plugins.relaylink.relays', ' ')

    def testSubstitute(self):
        self.assertNotError('config supybot.plugins.relaylink.substitutes ""')
        self.assertNotError('relaylink substitute foobar foo*bar')
        self.assertResponse('config supybot.plugins.relaylink.substitutes',
                            'foobar | foo*bar')
        self.assertNotError('relaylink substitute baz b*z')
        self.assertResponse('config supybot.plugins.relaylink.substitutes',
                            'foobar | foo*bar || baz | b*z')

    def testNoSubstitute(self):
        self.assertNotError('config supybot.plugins.relaylink.substitutes '
                            'foobar | foo*bar || baz | b*z')
        self.assertNotError('relaylink nosubstitute baz')
        self.assertResponse('config supybot.plugins.relaylink.substitutes',
                            'foobar | foo*bar')
        self.assertNotError('relaylink nosubstitute foobar')
        self.assertResponse('config supybot.plugins.relaylink.substitutes', ' ')



# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:

