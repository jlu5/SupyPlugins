###
# Copyright (c) 2016, James Lu <james@overdrivenetworks.com>
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

import supybot.utils as utils
from supybot.commands import wrap
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('MCInfo')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

import sys

if sys.version_info[0] >= 3:
    from urllib.parse import quote
else:
    from urllib import quote

from bs4 import BeautifulSoup

mcwiki_url = 'http://minecraft.gamepedia.com'

def format_text(text):
    text = text.replace('\xa0', '')
    text = utils.str.normalizeWhitespace(text)
    text = text.strip()
    return text

class MCInfo(callbacks.Plugin):
    """Fetches crafting recipes and other interesting information from the Minecraft Wiki."""
    threaded = True

    @wrap(['text'])
    def mcwiki(self, irc, msg, args, item):
        """
        Gets information from the Minecraft Wiki. This requires the Wikifetch plugin to be loaded.
        """
        wf = irc.getCallback("Wikifetch")

        if wf:
            # Use the Wikifetch plugin in this repository to lookup the information on the
            # item, tool, or thing given.
            text = wf._wiki(irc, msg, item, mcwiki_url)
            if _('may refer to') in text:
                irc.reply('%s seems to be a disambiguation page.' % text.split()[-1])
            else:
                irc.reply(text)
        else:
            irc.error("This command requires the Wikifetch plugin to be loaded.", Raise=True)

    def get_page(self, irc, item):
        """Returns the wiki page for the given item."""
        url = '%s/%s' % (mcwiki_url, quote(item))
        self.log.debug("MCInfo: using url %s", url)

        try:
            article = utils.web.getUrl(url)
        except utils.web.Error as e:
            if '404' in str(e):
                irc.error("Unknown item.", Raise=True)
            irc.error(e, Raise=True)

        soup = BeautifulSoup(article)
        return soup

    @wrap(['text'])
    def craft(self, irc, msg, args, item):
        """<item>

        Attempts to look up crafting information from the Minecraft wiki.
        """

        soup = self.get_page(irc, item)

        # Find the "Crafting table" displayed in the Wiki page showing how to craft the item.
        crafting_table = soup.find('table', attrs={"data-description": 'Crafting recipes'})
        if not crafting_table:
            irc.error("No crafting information found.", Raise=True)

        for tag in crafting_table.previous_siblings:
            # We only want the instructions on how to craft the item, not the items crafted WITH it.
            # TODO: maybe this behavior could be a different command?
            if tag.name == 'h3':
                t = tag.contents[0].get_text().strip()
                if t == 'Crafting ingredient':
                    irc.error("The item '%s' cannot be crafted." % item, Raise=True)

        # Get the first crafting result. TODO: optionally show all recipes if there are more than one.
        crafting_data = crafting_table.find_all('tr')[1]

        # Shows the text of the ingredients used to craft (e.g. "Glass + Any dye")
        ingredients = format_text(crafting_data.td.get_text())

        recipe = []

        # This tracks how long the longest item name is. Used for formatting the crafting table on
        # IRC with the right dimensions.
        maxitemlength = 0

        # Now, parse the layout of the 3x3 crafting grid the wiki shows for items.
        for rowdata in crafting_data.find_all('span', class_='mcui-row'):
            rowitems = []
            # Iterate over the rows of the crafting grid, and then the items in each.
            for itemslot in rowdata.children:

                itemlink = itemslot.a
                if itemlink:
                    # Item exists. Get the name of the item using the caption of its wiki page link.
                    itemname = itemlink.get('title')

                    # Replace spaces with hyphens in the display to make the display monospace.
                    #itemname = itemname.replace(' ', '-')

                    # Update the existing max item length if the length of the current one is
                    # greater.
                    if len(itemname) > maxitemlength:
                        maxitemlength = len(itemname)

                    rowitems.append(itemname)
                elif not itemslot.find('invslot-item'):
                    # Empty square.
                    rowitems.append('')
            if rowitems:
                recipe.append(rowitems)

        irc.reply("Recipe for %s uses: %s" % (ircutils.bold(item), ircutils.bold(ingredients)))
        for row in filter(any, recipe):  # Only output rows that have filled squares.
            # For each item, center its name based on the length of the longest item name in the
            # recipe. This gives the grid a more monospace-y feel.
            items = [s.center(maxitemlength, '-') for s in row]
            irc.reply('|%s|' % '|'.join(items))

    @wrap(['text'])
    def smelt(self, irc, msg, args, item):
        """<item>

        Attempts to look up smelting recipes from the Minecraft wiki.
        """

        soup = self.get_page(irc, item)

        # Find the "smelting" table displayed in the Wiki page.
        smelting_tables = soup.find_all('table', attrs={"data-description": 'Smelting recipes'})
        if not smelting_tables:
            irc.error("No smelting information found.", Raise=True)

        irc.reply("Smelting recipes involving %s:" % ircutils.bold(item))

        for table in smelting_tables:

            # Get the first smelting result.
            smelt_data = table.find_all('tr')[1]

            # Show the resulting item and the ingredients needed to smelt it.
            ingredients = format_text(smelt_data.td.get_text())
            try:
                result = format_text(smelt_data.th.get_text())
            except AttributeError:
                # If the text of the result item isn't explicitly shown, dig
                # deeper to extract the item name from the smelting table UI.
                smelting_ui = smelt_data.find_all('td')[1].div.span

                output = smelting_ui.find('span', class_='mcui-output')

                result = output.find('span', class_='sprite')
                result = result.get('title')

            irc.reply("%s: %s" % (ircutils.bold(result), ingredients))

    @wrap(['text'])
    def recipes(self, irc, msg, args, item):
        """<item>

        Returns Minecraft crafting recipes using the given item.
        """

        soup = self.get_page(irc, item)

        # First, look for the "Crafting ingredient" header (usually under a
        # section called "Usage"). Only here will we find the recipes for each
        # item.
        header = ''
        for header in soup.find_all('h3'):
            if header.span and header.span.get_text().strip().lower() == 'crafting ingredient':
                break
        else:
            irc.error("No recipes found.", Raise=True)

        for tag in header.next_siblings:
            # Only look at crafting table UIs after this header.
            if tag.name == 'table' and tag.get("data-description").lower() == 'crafting recipes':
                recipes = []

                # Iterate over all the recipes shown and get their names.
                for crafting_data in tag.find_all('tr')[1:]:
                    recipes.append(format_text(crafting_data.th.get_text()))

                # After we've found these results, we can stop looking for
                # crafting table UIs.
                break

        out_s = format('Recipes using %s include: %L', ircutils.bold(item), sorted(recipes))
        irc.reply(out_s)

Class = MCInfo


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
