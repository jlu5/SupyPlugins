###
# Copyright (c) 2015,2021 James Lu
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
import time
import uuid

from supybot.test import *

class RelayNextDBTestCase(PluginTestCase):
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
        self.assertError("relaynext set foobar #deV@overdrive-irc #DEV@overdrive-irc")
        self.assertError("relaynext set foobar #dev@overdrive-irc #DEV@OVERdrive-IRC")
        self.assertError("relaynext set foobar #dev@overdrive-irc #dev@OVERdrive-IRC")
        self.assertNotError("relaynext set abcd #moo@moo #MOO@mOO #test@test")
        self.assertRegexp("relaynext list", "#moo@moo")
        self.assertRegexp("relaynext list", "#test@test")

    def testAddCaseInsensitive(self):
        self.assertError("relaynext add foobar #deV@overdrive-irc #DEV@overdrive-irc")
        self.assertError("relaynext add foobar #dev@overdrive-irc #DEV@OVERdrive-IRC")
        self.assertError("relaynext add foobar #dev@overdrive-irc #dev@OVERdrive-IRC")
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


class RelayNextTestCase(PluginTestCase):
    plugins = ('RelayNext', 'Admin', 'Utilities')
    # Disable colours to make output checking more predictable
    config = {'plugins.RelayNext.color': False}
    timeout = 3

    def setUp(self):
        super().setUp()
        # These test network names are defined in scripts/supybot-test. Anything unknown will fail with:
        #     supybot.registry.NonExistentRegistryEntry: 'net1' is not a valid entry in 'supybot.networks'
        self.irc1 = getTestIrc("testnet1")
        self.chan1 = irclib.ChannelState()
        self.chan1name = '#' + uuid.uuid4().hex
        self.chan1.addUser(self.irc1.nick)  # Add the bot to the channel
        self.irc1.state.channels = {self.chan1name: self.chan1}

        self.irc2 = getTestIrc("testnet2")
        self.chan2 = irclib.ChannelState()
        self.chan2.addUser(self.irc2.nick)
        self.chan2name = '#' + uuid.uuid4().hex
        self.irc2.state.channels = {self.chan2name: self.chan2}
        self.assertNotError("relaynext set testRelay %s@testnet1 %s@testnet2" % (self.chan1name, self.chan2name))

    def getCommandResponse(self, irc):
        # Adapted from PluginTestCase._feedMsg() to account for other irc objects
        response = irc.takeMsg()
        fed = time.time()
        while response is None and time.time() - fed < self.timeout:
            time.sleep(0.01)
            drivers.run()
            response = irc.takeMsg()
        return response

    def testPrivmsg(self):
        msg = ircmsgs.privmsg(self.chan1name, "hello world", prefix='abc!def@ghi.jkl')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 <abc> hello world', output.args[1])

    def testPrivmsgAction(self):
        msg = ircmsgs.privmsg(self.chan2name, "\x01ACTION waves hello\x01", prefix='jlu5!~jlu5@user/jlu5')
        self.irc2.feedMsg(msg)  # irc2 is source
        output = self.getCommandResponse(self.irc1)
        self.assertEqual(self.chan1name, output.args[0])
        self.assertEqual('\x02[testnet2]\x02 * jlu5 waves hello', output.args[1])

    def testPrivmsgIgnoreCTCPs(self):  # irc2 is source
        self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, "\x01VERSION\x01", prefix='StatServ!StatServ@services.mytestnet.internal'))
        # Check that the first message isn't relayed
        self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, "dummy test message", prefix='StatServ!StatServ@services.mytestnet.internal'))
        output = self.getCommandResponse(self.irc1)
        self.assertEqual(self.chan1name, output.args[0])
        self.assertIn("dummy test", output.args[1])
        self.assertNotIn("VERSION", output.args[1])

    def testJoin(self):
        msg = ircmsgs.join(self.chan1name, prefix='testUser1!testuser@example.com')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 testUser1 (testuser@example.com) has joined %s' % self.chan1name, output.args[1])

    def testPartBare(self):
        msg = ircmsgs.part(self.chan1name, prefix='foo!bar@baz')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 foo (bar@baz) has left %s' % self.chan1name, output.args[1])

    def testPartWithReason(self):
        msg = ircmsgs.part(self.chan1name, 'foobar', prefix='foo!bar@baz')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 foo (bar@baz) has left %s (foobar)' % self.chan1name, output.args[1])

    def testTopic(self):
        with conf.supybot.plugins.relayNext.events.relayTopics.context(True):
            msg = ircmsgs.topic(self.chan1name, 'Some topic text', prefix='user5!~test@user/test')
            self.irc1.feedMsg(msg)
            output = self.getCommandResponse(self.irc2)
            self.assertEqual(self.chan2name, output.args[0])
            self.assertEqual('\x02[testnet1]\x02 user5 set topic on %s to: Some topic text' % self.chan1name, output.args[1])

    def testKick(self):
        msg = ircmsgs.kick(self.chan1name, 'soccerball', 'some ambiguous reason', prefix='foo!bar@foobar.example')
        self.irc1.state.nicksToHostmasks['soccerball'] = 'soccerball!dummy@dummy.test.client'
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 soccerball (dummy@dummy.test.client) has been kicked from %s by foo '
                         '(some ambiguous reason)' % self.chan1name, output.args[1])

    def testMode(self):
        msg = ircmsgs.mode(self.chan1name, ('-m'), prefix='foo!bar@foobar.example')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 foo (bar@foobar.example) set mode -m on %s' % self.chan1name, output.args[1])

    def testModeWithArgs(self):
        msg = ircmsgs.mode(self.chan1name, ('+ov', 'foo', 'foo'), prefix='foo!bar@foobar.example')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        self.assertEqual('\x02[testnet1]\x02 foo (bar@foobar.example) set mode +ov foo foo on %s' % self.chan1name, output.args[1])

    def testQuit(self):
        msg = ircmsgs.quit('goodbye', prefix='Tester1234!bar@example.org')
        self.irc1.feedMsg(msg)  # Because the source is not in the channel, their message doesn't get relayed
        self.chan1.addUser('nobody')
        msg = ircmsgs.quit('Leaving', prefix='Nobody!~nobody@test.user')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        # XXX: this should probably show the hostmask for consistency?
        self.assertEqual('\x02[testnet1]\x02 Nobody has quit (Leaving)', output.args[1])

    def testNick(self):
        msg = ircmsgs.nick('OldNick', prefix='oldnick!~ident@hidden-1234abcd.example.net')
        self.irc1.feedMsg(msg)  # Because the source is not in the channel, their message doesn't get relayed
        self.chan1.addUser('OldNick')
        msg = ircmsgs.nick('newnick', prefix='OldNick!~ident@hidden-1234abcd.example.net')
        self.irc1.feedMsg(msg)
        output = self.getCommandResponse(self.irc2)
        self.assertEqual(self.chan2name, output.args[0])
        # XXX: this should probably show the hostmask for consistency?
        self.assertEqual('\x02[testnet1]\x02 OldNick is now known as newnick', output.args[1])

    def testToggleEvents(self):
        with conf.supybot.plugins.relayNext.events.relayJoins.context(False):
            with conf.supybot.plugins.relayNext.events.relayParts.context(False):
                self.irc2.feedMsg(ircmsgs.join(self.chan2name, prefix='ChanServ!ChanServ@services.testnet.internal'))
                self.irc2.feedMsg(ircmsgs.part(self.chan2name, prefix='ChanServ!ChanServ@services.testnet.internal'))
                self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, 'Your channel is now registered =]', prefix='ChanServ!ChanServ@services.testnet.internal'))
        output = self.getCommandResponse(self.irc1)
        self.assertEqual(self.chan1name, output.args[0])
        self.assertEqual('\x02[testnet2]\x02 <ChanServ> Your channel is now registered =]', output.args[1])

    def testRelayColorNoHostmask(self):
        with conf.supybot.plugins.relayNext.color.context(True):
            with conf.supybot.plugins.relayNext.hostmasks.context(False):
                # Join message
                self.irc2.feedMsg(ircmsgs.join(self.chan2name, prefix='ChanServ!ChanServ@services.testnet.internal'))
                output = self.getCommandResponse(self.irc1)
                self.assertRegex(output.args[1], '\x02\\[\x03\\d{1,2}testnet2\x03\\]\x02 \x03\\d{1,2}ChanServ\x03 has joined')

                # PRIVMSG
                self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, 'Your channel is now registered =]', prefix='ChanServ!ChanServ@services.testnet.internal'))
                output = self.getCommandResponse(self.irc1)
                self.assertRegex(output.args[1], '\x02\\[\x03\\d{1,2}testnet2\x03\\]\x02 <\x03\\d{1,2}ChanServ\x03> Your channel is now registered =]')

                # Nick change
                self.chan2.addUser('old345')
                self.irc2.feedMsg(ircmsgs.nick('new123', prefix='old345!old345@Clk-12345678.lan'))
                output = self.getCommandResponse(self.irc1)
                self.assertRegex(output.args[1], '\x03\\d{1,2}old345\\x03 is now known as \x03\\d{1,2}new123\\x03')

    def testBlockHighlightsSimple(self):
        with conf.supybot.plugins.relayNext.noHighlight.context(True):
            with conf.supybot.plugins.relayNext.hostmasks.context(False):
                # Join message
                self.irc2.feedMsg(ircmsgs.join(self.chan2name, prefix='ChanServ!ChanServ@services.testnet.internal'))
                output = self.getCommandResponse(self.irc1)
                self.assertIn('C\u200bhanServ has joined', output.args[1])
                self.assertNotIn('ChanServ', output.args[1])

                # PRIVMSG
                self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, 'hi everyone', prefix='samplenick!user@host'))
                output = self.getCommandResponse(self.irc1)
                self.assertIn('<s\u200bamplenick>', output.args[1])
                self.assertNotIn('<samplenick>', output.args[1])

    def testBlockHighlightsNick(self):
        with conf.supybot.plugins.relayNext.noHighlight.context(True):
            with conf.supybot.plugins.relayNext.hostmasks.context(False):
                # Nick change
                self.chan2.addUser('old345')
                self.irc2.feedMsg(ircmsgs.nick('new123', prefix='old345!old345@Clk-12345678.lan'))
                output = self.getCommandResponse(self.irc1)
                self.assertIn('o\u200bld345', output.args[1])
                self.assertNotIn('old345', output.args[1])
                self.assertIn('n\u200bew123', output.args[1])
                self.assertNotIn('new123', output.args[1])

    def testBlockHighlightsKick(self):
        with conf.supybot.plugins.relayNext.noHighlight.context(True):
            with conf.supybot.plugins.relayNext.hostmasks.context(False):
                # KICK
                self.irc2.state.nicksToHostmasks['evilbot'] = 'evilbot!bot@test.client'
                self.chan2.addUser('evilbot')
                self.irc2.feedMsg(ircmsgs.kick(self.chan2name, 'evilbot', 'spam', prefix='a!b@c.d.e.f'))
                output = self.getCommandResponse(self.irc1)
                self.assertIn('e\u200bvilbot', output.args[1])
                self.assertNotIn('evilbot', output.args[1])
                self.assertIn('a\u200b', output.args[1])

    def testBlockHighlightsColor(self):
        with conf.supybot.plugins.relayNext.color.context(True):
            with conf.supybot.plugins.relayNext.noHighlight.context(True):
                # PRIVMSG
                self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, 'The quick brown fox jumps over the lazy dog', prefix='Limnoria!limnoria@bot/limnoria'))
                output = self.getCommandResponse(self.irc1)
                self.assertRegex(output.args[1], '<\x03\\d{1,2}L\u200bimnoria\x03>')

    def testShowPrefixes(self):  # currently only implemented for PRIVMSG
        with conf.supybot.plugins.relayNext.showPrefixes.context(True):
            users = {"foo": "@", "bar": "%", "baz": "+"}
            for nick, status in users.items():
                self.chan2.addUser(status+nick)
                self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, 'Hi', prefix='%s!user@monotonous.example' % nick))
                output = self.getCommandResponse(self.irc1)
                self.assertIn('<%s%s>' % (status, nick), output.args[1])
                self.assertNotIn('<%s>' % nick, output.args[1])

    def testShowPrefixesColorNoHighlight(self):
        with conf.supybot.plugins.relayNext.showPrefixes.context(True):
            with conf.supybot.plugins.relayNext.color.context(True):
                with conf.supybot.plugins.relayNext.noHighlight.context(True):
                    users = {"foo": "@", "bar": "%", "baz": "+"}
                    for nick, status in users.items():
                        self.chan2.addUser(status+nick)
                        self.irc2.feedMsg(ircmsgs.privmsg(self.chan2name, 'Hi', prefix='%s!user@monotonous.example' % nick))
                        output = self.getCommandResponse(self.irc1)
                        self.assertRegex(output.args[1], '<[%s]\x03\\d{1,2}%s\u200b%s\x03>' % (status, nick[0], nick[1:]))

    def testIgnore(self):
        self.assertNotError("admin ignore add *!*@*/bot/*")
        self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, "Message from bot", prefix='testbot!testbot@user/test/bot/testbot'))
        self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, "Message from user", prefix='tester!test@user/test'))
        output = self.getCommandResponse(self.irc2)
        self.assertEqual('\x02[testnet1]\x02 <tester> Message from user', output.args[1])

    def testIgnoreRegexp(self):
        cfgvar = conf.supybot.plugins.relayNext.ignoreRegexp
        try:
            cfgvar.set("m/xnopyt/")
            self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, "!ud xnopyt", prefix='abc!def@efg.user'))
            self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, "!ud IRC", prefix='abc!def@efg.user'))
            output = self.getCommandResponse(self.irc2)
            self.assertIn('<abc> !ud IRC', output.args[1])
        finally:
            cfgvar.set(cfgvar._default)

    @unittest.skip("Not working yet...")
    def testRelaySelfMessages(self):
        self.irc1.nick = 'RelayBot'
        self.chan1.addUser('RelayBot')
        self.chan1.addUser('caller')
        with conf.supybot.plugins.relayNext.events.relaySelfMessages.context(True):
            cmd = "RelayBot: echo abcd"
            self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, cmd, prefix='caller!caller@abc.internal'))
            output = self.getCommandResponse(self.irc2)
            self.assertIn('<caller> ' + cmd, output.args[1])
            output = self.getCommandResponse(self.irc2)
            self.assertIn('<RelayBot> abcd', output.args[1])
        with conf.supybot.plugins.relayNext.events.relaySelfMessages.context(False):
            self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, "RelayNext: echo xyzzy", prefix='caller!caller@abc.internal'))
            self.irc1.feedMsg(ircmsgs.privmsg(self.chan1name, "\o/", prefix='botty!mcbotface@bots.fancy.example'))
            output = self.getCommandResponse(self.irc2)
            self.assertIn('<botty> \o/', output.args[1])


    # TODO: relaySelfMessages
    # TODO: !nicks command
    # TODO: antiflood
    # TODO: announcement routing (trigger relay() manually)
    # TODO: a >= 3 net relay?

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
