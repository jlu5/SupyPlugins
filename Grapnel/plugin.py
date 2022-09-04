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

import json
import secrets
import sqlite3
import urllib.parse

from supybot import ircmsgs, ircutils, callbacks, httpserver, log, world
from supybot.commands import conf, wrap
from supybot.i18n import PluginInternationalization


_ = PluginInternationalization('Grapnel')

class GrappleHTTPCallback(httpserver.SupyHTTPServerCallback):
    name = 'Grapnel'

    def _send_response(self, handler, code, text, extra_headers=None):
        handler.send_response(code)
        handler.send_header('Content-type', 'text/plain')
        if extra_headers:
            for header_pair in extra_headers:
                handler.send_header(*header_pair)
        handler.end_headers()
        handler.wfile.write(text.encode('utf-8'))
        handler.wfile.write(b'\n')

    def doPost(self, handler, path, form=None):
        try:
            log.info(path)
            if handler.headers['Content-type'] != 'application/json':
                self._send_response(handler, 400, "Bad HTTP Content-Type (expected JSON)")
                return
            try:
                data = json.loads(form.decode('utf-8'))
            except json.JSONDecodeError as e:
                self._send_response(handler, 400, f"Invalid JSON input: {e}")
                return
            if not isinstance(data, dict):
                self._send_response(handler, 400, "Incorrect JSON data type (expected object)")
                return
            if not (text := data.get('text')):
                self._send_response(handler, 400, "Message is missing a text field")
                return

            url_parts = urllib.parse.urlparse(path)
            url_qs = urllib.parse.parse_qs(url_parts.query)
            hookID = url_parts.path.strip('/')
            log.error(str(url_qs))

            if not (req_tokens := url_qs.get('token')):
                self._send_response(handler, 401, "Missing webhook token")
                return

            # Optional sender for formatting
            sender_name = url_qs.get('sender', ['<unknown>'])[0]

            cur = self.plugin.conn.cursor()  # pylint: disable=no-member
            cur.execute("""
            SELECT network, channel, token FROM webhooks
            WHERE id=?
            """, (hookID,))

            result = cur.fetchone()
            if not result:
                self._send_response(handler, 404, f"No such webhook ID {hookID!r}")
                return
            network, channel, real_token = result

            # query string keys can contain a list of values
            if req_tokens[0] != real_token:
                self._send_response(handler, 403, "Incorrect webhook token")
                return

            if not (irc := world.getIrc(network)):
                self._send_response(handler, 500, f"Network {network!r} is not connected")
                return

            fields = {
                "text": str(text),
                "name": sender_name
            }
            # pylint: disable=no-member
            tmpl = self.plugin.registryValue("format", channel=channel, network=network)
            out_s = ircutils.standardSubstitute(irc, None, tmpl, env=fields)
            if not out_s:
                log.warning("Grapnel: output text for webhook %s / %s@%s is empty", hookID, channel, network)
                self._send_response(handler, 500, "Output text is empty (misconfigured output template?)")
                return
            m = ircmsgs.privmsg(channel, out_s)
            irc.queueMsg(m)

            self._send_response(handler, 200, "OK")

        except:
            self._send_response(handler, 500, "Unspecified internal error")
            raise

    def doGet(self, handler, path):
        self._send_response(handler, 405, "Only POST requests are supported by this service",
                            extra_headers=[('Allow', 'POST')])

HTTP_ENDPOINT_NAME = 'grapnel'

# https://docs.python.org/3.10/library/secrets.html#how-many-bytes-should-tokens-use
TOKEN_LENGTH = 32

class Grapnel(callbacks.Plugin):
    """Grapnel plugin: announce Slack-compatible webhooks to IRC"""
    threaded = False  # sqlite3 not thread safe for writes

    def __init__(self, irc):
        super().__init__(irc)

        self.callback = GrappleHTTPCallback()
        self.callback.plugin = self
        httpserver.hook(HTTP_ENDPOINT_NAME, self.callback)

        dbfile = conf.supybot.directories.data.dirize("Grapnel.sqlite")
        # ASSUME: writes only come from main thread handling IRC commands
        self.conn = sqlite3.connect(dbfile, check_same_thread=False)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS webhooks(
            id INTEGER PRIMARY KEY,
            network TEXT,
            channel TEXT,
            token TEXT
        )
        """)

    def die(self):
        httpserver.unhook(HTTP_ENDPOINT_NAME)
        self.conn.close()
        super().die()

    def _format_url(self, hookID, token):
        baseurl = self.registryValue("baseURL")
        url = urllib.parse.urljoin(baseurl, f"/{HTTP_ENDPOINT_NAME}/{hookID}?" + urllib.parse.urlencode({
            'token': token,
            'sender': 'your-cool-app-name'
        }))
        return url

    @wrap(['networkIrc', 'channel', 'admin'])
    def add(self, irc, msg, args, networkIrc, channel):
        """[<network>] [<channel>]

        Creates a new Slack-compatible webhook endpoint for a given network + channel.
        <network> and <channel> default to the current network and channel if not specified.
        """
        if not self.registryValue("baseurl"):
            raise callbacks.Error(_("Webhook base URL missing; set the config option plugins.grapnel.baseurl"))

        network = networkIrc.network
        token = secrets.token_hex(TOKEN_LENGTH)
        channel = ircutils.toLower(channel)

        cur = self.conn.cursor()
        cur.execute("""
        INSERT INTO webhooks(network, channel, token)
        VALUES (?, ?, ?)
        """, (network, channel, token))
        self.conn.commit()
        newID = cur.lastrowid
        url = self._format_url(newID, token)

        #s = _("Webhook #%d created. This link (with the token) will only be shown once; keep it private!: %s") % (newID, url)
        s = _("Webhook #%d created. Keep this link private! %s") % (newID, url)
        log.debug("Grapnel: created webhook %s for %s@%s: %s", newID, channel, network, url)
        irc.reply(s, private=True)

    @wrap(['networkIrc', 'channel', 'admin'])
    def listhooks(self, irc, msg, args, networkIrc, channel):
        """[<network>] [<channel>]

        Lists webhooks set on the network + channel pair.
        <network> and <channel> default to the current network and channel if not specified.
        """
        network = networkIrc.network
        channel = ircutils.toLower(channel)
        cur = self.conn.cursor()
        cur.execute("""
        SELECT id FROM webhooks
        WHERE network=? AND channel=?
        """, (network, channel))
        results = [row[0] for row in cur.fetchall()]
        if results:
            results_s = ' '.join([f"#{i}" for i in results])
        else:
            results_s = _('(none)')
        irc.reply(_("Webhooks for %s@%s: %s") % (channel, network, results_s))

    @wrap(['nonNegativeInt', 'admin'])
    def get(self, irc, msg, args, hookID):
        """<webhook ID>

        Returns metadata and the URL for the webhook ID.
        """
        cur = self.conn.cursor()
        cur.execute("""
        SELECT * FROM webhooks
        WHERE id=?
        """, (hookID,))
        result = cur.fetchone()
        if result is None:
            irc.error(_("No such webhook #%d.") % hookID)
        else:
            __, network, channel, token = result
            url = self._format_url(hookID, token)
            s = _("Webhook #%d for %s@%s: %s") % (hookID, channel, network, url)
            irc.reply(s, private=True)

    @wrap(['nonNegativeInt', 'admin'])
    def resettoken(self, irc, msg, args, hookID):
        """<webhook ID>

        Regenerates the token for the given webhook ID.
        """
        cur = self.conn.cursor()
        token = secrets.token_hex(TOKEN_LENGTH)
        cur.execute("""
        UPDATE webhooks
        SET token=?
        WHERE id=?
        """, (token, hookID))
        self.conn.commit()
        if cur.rowcount:
            url = self._format_url(hookID, token)
            s = _("Updated webhook #%d: %s") % (hookID, url)
            irc.reply(s, private=True)
        else:
            irc.error(_("No such webhook #%d.") % hookID)

    @wrap(['nonNegativeInt', 'admin'])
    def remove(self, irc, msg, args, hookID):
        """<webhook ID>

        Removes the given webhook ID.
        """
        cur = self.conn.cursor()
        cur.execute("""
        DELETE FROM webhooks
        WHERE id=?
        """, (hookID,))
        self.conn.commit()
        if cur.rowcount:
            irc.replySuccess()
        else:
            irc.error(_("No such webhook #%d.") % hookID)


Class = Grapnel


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
