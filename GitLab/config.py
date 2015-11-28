###
# Copyright (c) 2015, Moritz Lipp
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

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Gitlab')
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
    conf.registerPlugin('Gitlab', True)


Gitlab = conf.registerPlugin('Gitlab')

# Settings
conf.registerChannelValue(Gitlab, 'projects',
    registry.Json({}, _("""List of projects""")))

# Format
conf.registerGroup(Gitlab, 'format')

conf.registerChannelValue(Gitlab.format, 'push',
    registry.String(_("""\x02[{project[name]}]\x02 {user_name} pushed \x02{total_commits_count} commit(s)\x02 to \x02{ref}\x02:"""),
                    _("""Format for push events.""")))
conf.registerChannelValue(Gitlab.format, 'commit',
    registry.String(_("""\x02[{project[name]}]\x02 {short_id} \x02{short_message}\x02 by {author[name]}"""),
                    _("""Format for commits.""")))

conf.registerChannelValue(Gitlab.format, 'tag',
    registry.String(_("""\x02[{project[name]}]\x02 {user_name} created a new tag {ref}"""),
                    _("""Format for tag push events.""")))

conf.registerChannelValue(Gitlab.format, 'issue-open',
    registry.String(_("""\x02[{project[name]}]\x02 Issue \x02#{issue[id]} {issue[title]}\x02 created by {user[name]} {issue[url]}"""),
                    _("""Format for issue/open events.""")))
conf.registerChannelValue(Gitlab.format, 'issue-update',
    registry.String(_("""\x02[{project[name]}]\x02 Issue \x02#{issue[id]} {issue[title]}\x02 updated by {user[name]} {issue[url]}"""),
                    _("""Format for issue/update events.""")))
conf.registerChannelValue(Gitlab.format, 'issue-close',
    registry.String(_("""\x02[{project[name]}]\x02 Issue \x02#{issue[id]} {issue[title]}\x02 closed by {user[name]} {issue[url]}"""),
                    _("""Format for issue/close events.""")))
conf.registerChannelValue(Gitlab.format, 'issue-reopen',
    registry.String(_("""\x02[{project[name]}]\x02 Issue \x02#{issue[id]} {issue[title]}\x02 reopend by {user[name]} {issue[url]}"""),
                    _("""Format for issue/reopen events.""")))

conf.registerChannelValue(Gitlab.format, 'merge-request-open',
    registry.String(_("""\x02[{project[name]}]\x02 Merge request \x02#{merge_request[id]} {merge_request[title]}\x02 created by {user[name]} {merge_request[url]}"""),
                    _("""Format for merge-request/open events.""")))
conf.registerChannelValue(Gitlab.format, 'merge-request-update',
    registry.String(_("""\x02[{project[name]}]\x02 Merge request \x02#{merge_request[id]} {merge_request[title]}\x02 updated by {user[name]} {merge_request[url]}"""),
                    _("""Format for merge-request/open events.""")))
conf.registerChannelValue(Gitlab.format, 'merge-request-close',
    registry.String(_("""\x02[{project[name]}]\x02 Merge request \x02#{merge_request[id]} {merge_request[title]}\x02 closed by {user[name]} {merge_request[url]}"""),
                    _("""Format for merge-request/open events.""")))
conf.registerChannelValue(Gitlab.format, 'merge-request-reopen',
    registry.String(_("""\x02[{project[name]}]\x02 Merge request \x02#{merge_request[id]} {merge_request[title]}\x02 reopened by {user[name]} {merge_request[url]}"""),
                    _("""Format for merge-request/open events.""")))
conf.registerChannelValue(Gitlab.format, 'merge-request-merge',
    registry.String(_("""\x02[{project[name]}]\x02 Merge request \x02#{merge_request[id]} {merge_request[title]}\x02 merged by {user[name]} {merge_request[url]}"""),
                    _("""Format for merge-request/open events.""")))

conf.registerChannelValue(Gitlab.format, 'note-merge-request',
    registry.String(_("""\x02[{project[name]}]\x02 {user[name]} commented on Merge request \x02#{merge_request[id]} {merge_request[title]}\x02 {note[url]}"""),
                    _("""Format for note/merge-request events.""")))
conf.registerChannelValue(Gitlab.format, 'note-commit',
    registry.String(_("""\x02[{project[name]}]\x02 {user[name]} commented on Commit \x02#{commit[id]}\x02 {commit[url]}"""),
                    _("""Format for note/commit events.""")))
conf.registerChannelValue(Gitlab.format, 'note-issue',
    registry.String(_("""\x02[{project[name]}]\x02 {user[name]} commented on Issue \x02#{issue[id]} {issue[title]}\x02 {note[url]}"""),
                    _("""Format for note/issue events.""")))
conf.registerChannelValue(Gitlab.format, 'note-snippet',
    registry.String(_("""\x02[{project[name]}]\x02 {user[name]} commented on Snippet \x02#{snippet[id]} {snippet[title]}\x02 {note[url]}"""),
                    _("""Format for note/snippet events.""")))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
