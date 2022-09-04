###
# Copyright (c) 2022, James Lu <james@overdrivenetworks.com>
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

import io
import json
import re
import urllib.parse

from supybot import conf
from supybot.test import ChannelHTTPPluginTestCase, FakeHTTPConnection, TestRequestHandler

TEST_BASEURL = 'http://grapnel.test'

class GrapnelTestCase(ChannelHTTPPluginTestCase):
    plugins = ('Grapnel',)
    config = {
        'plugins.grapnel.baseurl': TEST_BASEURL
    }
    timeout = 10

    # Like HTTPPluginTestCase.request, but with JSON Content-Type header and data
    def jsonPost(self, url, json_data):
        assert url.startswith('/')
        wfile = io.BytesIO()
        rfile = io.BytesIO()
        # wfile and rfile are reversed in Limnoria's HTTPPluginTestCase.request too?
        connection = FakeHTTPConnection(wfile, rfile)
        headers = {'Content-Type': 'application/json'}
        connection.request('POST', url, json_data, headers)
        rfile.seek(0)
        handler = TestRequestHandler(rfile, wfile)
        wfile.seek(0)
        return (handler._response, wfile.read()) # pylint: disable=protected-access

    # def setUp(self):
    #     super().setUp()
    #     self.myVerbose = verbosity.MESSAGES

    def _getLinkFragment(self, m):
        url_re = re.search(fr'{TEST_BASEURL}(\/grapnel\/\d+\?.*)', m.args[1])
        url_fragment = url_re.group(1)
        assert url_fragment
        return url_fragment

    def _addHook(self, channel='#test'):
        m = self.assertRegexp(f"grapnel add {channel}", fr"Webhook #\d+ created.*{TEST_BASEURL}/grapnel")
        return self._getLinkFragment(m)

    def testPOSTSuccess(self):
        url_fragment = self._addHook()
        (respCode, body) = self.jsonPost(url_fragment, json.dumps({"text": "123456"}))
        self.assertEqual(respCode, 200, body.decode())
        self.assertSnarfRegexp(' ', r'\[.*?\] 123456')

    def testPOSTCustomFormat(self):
        url_fragment = self._addHook()
        sp = urllib.parse.urlsplit(url_fragment)
        sp_query = urllib.parse.parse_qs(sp.query)
        #print("OLD", url_fragment, sp_query)
        url_fragment = sp.path + '?' + urllib.parse.urlencode({
            'token': sp_query['token'][0], 'sender': 'foobar'})
        #print("NEW", url_fragment)

        with conf.supybot.plugins.grapnel.format.context("Limnoria says: [$name] $text"):
            (respCode, body) = self.jsonPost(url_fragment, json.dumps({"text": "123456"}))
            self.assertEqual(respCode, 200, body.decode())
            self.assertSnarfResponse(' ', 'Limnoria says: [foobar] 123456')

    def testPOSTInvalidJSON(self):
        url_fragment = self._addHook()
        (respCode, body) = self.jsonPost(url_fragment, "<html></html>")
        self.assertEqual(respCode, 400, body.decode())
        self.assertSnarfNoResponse(' ')

    def testPOSTMissingToken(self):
        url_fragment = self._addHook()

        sp = urllib.parse.urlsplit(url_fragment)
        url_fragment = sp.path

        (respCode, body) = self.jsonPost(url_fragment, json.dumps({"text": "hello world"}))
        self.assertEqual(respCode, 401, body.decode())
        self.assertSnarfNoResponse(' ')

    def testPOSTWrongToken(self):
        url_fragment = self._addHook()

        # parse the URL and change the token
        sp = urllib.parse.urlsplit(url_fragment)
        url_fragment = sp.path + '?' + urllib.parse.urlencode({'token': 'obvious-incorrect'})

        (respCode, body) = self.jsonPost(url_fragment, json.dumps({"text": "hello world"}))
        self.assertEqual(respCode, 403, body.decode())
        self.assertSnarfNoResponse(' ')

    def testPOSTUnknownHookID(self):
        url_fragment = self._addHook()

        # parse the URL and change the path
        sp = urllib.parse.urlsplit(url_fragment)
        url_fragment = '/grapnel/12345?' + sp.query

        (respCode, body) = self.jsonPost(url_fragment, json.dumps({"text": "hello world"}))
        self.assertEqual(respCode, 404, body.decode())
        self.assertSnarfNoResponse(' ')

    def testPOSTBadContentType(self):
        url_fragment = self._addHook()
        (respCode, body) = self.request(url_fragment, method='POST')
        self.assertEqual(respCode, 400, body.decode())
        self.assertSnarfNoResponse(' ')

    def testGet(self):
        url_fragment_1 = self._addHook()
        url_fragment_2 = self._addHook(channel='#limnoria')
        self.assertRegexp('grapnel get 1', fr'Webhook #1 for #test@test.*{re.escape(url_fragment_1)}')
        self.assertRegexp('grapnel get 2', fr'Webhook #2 for #limnoria@test.*{re.escape(url_fragment_2)}')

    def testRemove(self):
        url_fragment_1 = self._addHook(channel='#bots')
        url_fragment_2 = self._addHook(channel='#bots')
        url_fragment_3 = self._addHook(channel='#bots')
        self.assertNotError('grapnel remove 2')
        self.assertRegexp('grapnel listhooks #bots', '#1 #3$')

        # check that the removed hook errors
        (respCode, body) = self.jsonPost(url_fragment_2, json.dumps({"text": "this goes nowhere"}))
        self.assertEqual(respCode, 404, body.decode())
        self.assertSnarfNoResponse(' ')

        # can't remove it twice
        self.assertError('grapnel remove 2')

    def testListAndCaseNormalization(self):
        url_fragment_1 = self._addHook(channel='#dev')
        url_fragment_2 = self._addHook(channel='#Dev')
        url_fragment_3 = self._addHook(channel='#limnoria')
        self.assertResponse('grapnel listhooks #dev', 'Webhooks for #dev@test: #1 #2')
        self.assertResponse('grapnel listhooks #DEV', 'Webhooks for #dev@test: #1 #2')
        self.assertResponse('grapnel listhooks #Limnoria', 'Webhooks for #limnoria@test: #3')
        self.assertRegexp('grapnel listhooks #', r'\#\@test.*\(none\)')

    def testResetTokenWorks(self):
        url_fragment_old = self._addHook()
        m = self.assertRegexp("grapnel resettoken 1", fr"{TEST_BASEURL}/grapnel")
        url_fragment_new = self._getLinkFragment(m)

        # check that they're the same hook ID
        self.assertNotEqual(url_fragment_old, url_fragment_new, "Webhook URLs should be different")
        self.assertIn("grapnel/1?", url_fragment_old)
        self.assertIn("grapnel/1?", url_fragment_new)

        # old token gives 403
        (respCode, body) = self.jsonPost(url_fragment_old, json.dumps({"text": "hello world"}))
        self.assertEqual(respCode, 403, body.decode())
        self.assertSnarfNoResponse(' ')
        # new token is OK
        (respCode, body) = self.jsonPost(url_fragment_new, json.dumps({"text": "the game"}))
        self.assertEqual(respCode, 200, body.decode())

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
