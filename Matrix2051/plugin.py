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

from supybot import utils, plugins, ircutils, callbacks, ircmsgs
from supybot.commands import wrap, getopts
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Matrix2051')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Matrix2051(callbacks.Plugin):
    """Extended support for Matrix2051"""

    @wrap(['channel'])
    def dmroom(self, irc, msg, args, channel):
        """[<channel>]

        Sets your DM room to the provided channel.
        """
        if not self.registryValue("enabled", network=irc.network):
            irc.error("DM room routing is not enabled on this server", Raise=True)

        if not hasattr(irc.state, '_dmroom_map'):
            irc.state._dmroom_map = {}
        account = msg.server_tags.get('account')
        if not account:
            irc.error("No account tag from your message", Raise=True)

        # XXX doesn't work, bot doesn't think it's in the channel?
        # if len(irc.state.channels[channel].users) != 2:
        #     irc.error("Only DM rooms with 2 members are supported", Raise=True)

        irc.state._dmroom_map[account] = channel
        irc.replySuccess("Mapped %s to %s" % (account, channel))

    @wrap(['admin', getopts({'clear': ''})])
    def dmrooms(self, irc, msg, args, optlist):
        """[--clear]

        List or clear all configured DM rooms on this network.
        """
        if not self.registryValue("enabled", network=irc.network):
            irc.error("DM room routing is not enabled on this server", Raise=True)

        room_map = getattr(irc.state, '_dmroom_map', None)
        opts = dict(optlist)
        if opts.get('clear'):
            irc.state._dmroom_map = {}
            irc.replySuccess()
        else:
            # too lazy to format this better
            irc.reply(str(room_map), private=True)

    def inFilter(self, irc, msg):
        if self.registryValue("enabled", network=irc.network) \
                and msg.command in {'PRIVMSG', 'NOTICE'}:
            if 'server-time' in irc.state.capabilities_ack and msg.time < irc.startedAt:
                self.log.debug("Matrix2051: dropping replayed %s from before initial connect (%s < %s)",
                               msg.command, msg.time, irc.startedAt)
                return
            if room_map := getattr(irc.state, '_dmroom_map', None):
                account = msg.server_tags.get('account')
                dmroom = room_map.get(account)
                if account and dmroom == msg.args[0]:
                    self.log.debug("Matrix2051: rewriting incoming %s from %s -> %s",
                                   msg.command, dmroom, account)
                    new_msg = ircmsgs.IrcMsg(args=(irc.nick, *msg.args[1:]), msg=msg)
                    return new_msg
        return msg

    def outFilter(self, irc, msg):
        if self.registryValue("enabled", network=irc.network) and \
                msg.command in {'PRIVMSG', 'NOTICE'}:
            if room_map := getattr(irc.state, '_dmroom_map', None):
                target = msg.args[0]  # target may be user MXID
                if not irc.isChannel(target):
                    if dmroom := room_map.get(target):
                        self.log.debug("Matrix2051: rewriting outgoing %s to %s -> %s",
                                        msg.command, target, dmroom)
                        new_msg = ircmsgs.IrcMsg(args=(dmroom, *msg.args[1:]), msg=msg)
                        return new_msg
                    self.log.warning("Matrix2051: attempted to send message to %s but "
                                     "could not find a suitable room", target, dmroom)
        return msg


Class = Matrix2051


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
