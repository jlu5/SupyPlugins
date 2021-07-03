Grabs data from Wikipedia and other MediaWiki-powered sites. This plugin requires the [lxml](https://lxml.de/installation.html) Python module.

## Usage

```
<jlu5> `wiki apple
<Atlas> The apple tree (Malus domestica) is a deciduous tree in the rose family best known for its sweet, pomaceous fruit, the apple. It is cultivated worldwide as a fruit tree, and is the most widely grown species in the genus Malus. The tree originated in Central Asia, where its wild ancestor, Malus sieversii, is still found today. Apples have been grown for thousands of years in Asia and Europe, and were (1 more message)
```

You can also add other sites using the `--site` option:

```
<jlu5> `wiki --site wiki.archlinux.org Bash
<Atlas> Bash (Bourne-again Shell) is a command-line shell/programming language by the GNU Project. Its name is a homaging reference to its predecessor: the long-deprecated Bourne shell. Bash can be run on most UNIX-like operating systems, including GNU/Linux. Retrieved from <https://wiki.archlinux.org/index.php?title=Bash>
```

```
<jlu5> `wiki --site community.wikia.com Help:Wikitext
<Atlas> Wikitext is the main markup language used to format content on wikias. It can be used to add photos, tables, bold styles, links, and other visual changes. Retrieved from <http://community.wikia.com/wiki/Help:Wikitext>
```
