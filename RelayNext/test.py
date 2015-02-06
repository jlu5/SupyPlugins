###
# Copyright (c) 2015, James Lu
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

class RelayNextTestCase(PluginTestCase):
    plugins = ('RelayNext',)

    def testAdd(self):
        self.assertNotError("relaynext add test #channel1@somenet #channel2@othernet")
        self.assertRegexp("relaynext list", "#channel1@somenet")
        self.assertRegexp("relaynext list", "#channel2@othernet")
        # Incorrect amount of arguments
        self.assertError("relaynext add test")
        self.assertError("relaynext add test afdasfader agkajeoig #validchannel@othernet")
        self.assertError("relaynext add nonexistant-relay #channel1@somenet")

    def testSet(self):
        self.assertNotError("relaynext set test #channel1@somenet #channel2@othernet")
        self.assertRegexp("relaynext list", "#channel1@somenet")
        self.assertRegexp("relaynext list", "#channel2@othernet")
        self.assertError("relaynext set test")
        self.assertError("relaynext set test #channel1@somenet")
    
    def testList(self):
        # This should error if no relays are defined
        self.assertError("relaynext list")
        self.assertNotError("relaynext set abcd #moo@moo #test@test")
        self.assertRegexp("relaynext list", "#moo@moo")
        self.assertRegexp("relaynext list", "#test@test")

    def testSetCaseInsensitive(self):
        self.assertError("relaynext set derp #dev@overdrive-irc #DEV@OVERdrive-IRC")
        self.assertNotError("relaynext set abcd #moo@moo #MOO@mOO #test@test")
        self.assertRegexp("relaynext list", "#moo@moo")
        self.assertRegexp("relaynext list", "#test@test")

    def testAddCaseInsensitive(self):
        self.assertError("relaynext add derp #dev@overdrive-irc #DEV@OVERdrive-IRC")
        self.assertNotError("relaynext add abcd #moo@moo #MOO@mOO #test@test")
        self.assertRegexp("relaynext list", "#moo@moo")
        self.assertRegexp("relaynext list", "#test@test")

    def testRemoveEntireRelay(self):
        self.assertError("relaynext remove some-relay")
        self.assertNotError("relaynext add some-relay #channel1@somenet #channel2@othernet #abcd@test123")
        # 'remove' without arguments removes an entire relay
        self.assertNotError("relaynext remove some-relay")
        # No relays should be defined now.
        self.assertError("relaynext list")

    def testRemoveChannelsFromExistingRelay(self):
        self.assertNotError("relaynext add some-relay #channel1@somenet #channel2@othernet #abcd@test123")
        # This should give a warning (removing a channel that's not in the specified relay)
        self.assertRegexp("relaynext remove some-relay #asfdafaergea@random",
                          'not found in the original relay: '
                          '#asfdafaergea@random')
        self.assertNotError("relaynext remove some-relay #abcd@test123")
        self.assertRegexp("relaynext list", "#channel1@somenet")
        self.assertRegexp("relaynext list", "#channel2@othernet")
        self.assertNotRegexp("relaynext list", "#abcd@test123")

    def testAutoremoveWhenLessThanTwoChannels(self):
        self.assertNotError("relaynext add some-relay #channel1@somenet #channel2@othernet #abcd@test123")
        self.assertNotError("relaynext remove some-relay #abcd@test123 #channel2@othernet")
        self.assertError("relaynext list")

    def testAddChannelsToExistingRelay(self):
        self.assertNotError("relaynext add test #channel1@somenet #channel2@othernet")
        self.assertNotError("relaynext add test #somewhereElse@mynet")
        self.assertRegexp("relaynext list", "#channel1@somenet")
        self.assertRegexp("relaynext list", "#channel2@otherne")
        self.assertRegexp("relaynext list", "#somewhereelse@mynet")

    def testClear(self):
        self.assertNotError("relaynext set test #channel1@somenet #channel2@othernet")
        self.assertNotError("relaynext clear")
        self.assertError("relaynext list")

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
