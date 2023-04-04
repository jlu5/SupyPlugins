Fetch content from MediaWiki-powered sites (Wikipedia, Fandom, Wiki.gg, etc.). This plugin requires [Beautiful Soup 4](http://www.crummy.com/software/BeautifulSoup/bs4/doc/) and [mwparserfromhell](https://mwparserfromhell.readthedocs.io/): `pip3 install beautifulsoup4 mwparserfromhell`

## Usage

### Wikipedia

```
<jlu5> `wiki apple
<Atlas> An apple is an edible fruit produced by an apple tree (Malus domestica). Apple trees are cultivated worldwide and are the most widely grown species in the genus Malus. The tree originated in Central Asia, where its wild ancestor, Malus sieversii, is still found today. Apples have been grown for thousands of years in Asia and Europe and were brought to North America by European colonists. Apples have religious and mythological significance in many cultures, including Norse, Greek, and European Christian tradition. - https://en.wikipedia.org/wiki/Apple
```

You can set the default Wikipedia language with `config plugins.Wikifetch.wikipedia.lang <langcode>`

### Fandom

```
<jlu5> `fandom minecraft Apple
<Atlas> Obsidian is a block found in all dimensions or created when water flows over a lava source. It has high hardness and blast resistance, rendering it immune to normal explosions. Obsidian is used for crafting and to make the frame for a nether portal. It can only be obtained by mining it with a Diamond or Netherite Pickaxe. - https://minecraft.fandom.com/wiki/Obsidian
```

### Wiki.gg

```
<jlu5> `wikigg terraria Chest
<Atlas> Chests are storage items that each hold up to 40 item stacks in rows of 10×4 / 5×8 / 5×4 (only 20 item stacks). Chests can be freed with any pickaxe or drill, but only when empty. It is impossible to destroy the blocks underneath a placed Chest that contains items. - https://terraria.wiki.gg/wiki/Chests
```

### Any MediaWiki site

Wikifetch can read data from any MediaWiki site that has a public API. However, you must pass in the API URL, which may
or may not be under the same path as the wiki pages you read in a browser. You can usually find the path to the API by
opening the Source code of any wiki page and looking for links ending with `api.php`.

To make fetching content from other sites easier, you can always add a Limnoria Alias: e.g. `@aka add yourwiki "customwiki your-favourite-site/api.php $*"`

#### Example: Arch Linux Wiki (`/api.php`)

```
<jlu5> `customwiki https://wiki.archlinux.org/api.php KDE
<Atlas> KDE is a software project currently comprising a desktop environment known as Plasma, a collection of libraries and frameworks (KDE Frameworks) and several applications (KDE Applications) as well. KDE upstream has a well maintained UserBase wiki. Detailed information about most KDE applications can be found there. - https://wiki.archlinux.org/index.php?title=KDE
```

#### Example: Miraheze Sites (`/w/api.php`)

```
<jlu5> `customwiki https://www.thesimswiki.com/w/api.php Library
<Atlas> A library is a community lot and lot assignment in The Sims 3 and The Sims 4 that allows Sims to read books, but not to bring them home. - https://www.thesimswiki.com/w/index.php?title=Library
```
