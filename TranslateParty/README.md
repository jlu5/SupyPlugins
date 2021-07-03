## Translate Party

**Note: This plugin requires Python 3!**

Translate party sticks text through multiple rounds of Google Translate, in order to get
some amusing results. It automatically picks a list of languages to go through, and translates
back and forth between them quite a few times. This guarantees that the result will be different
every time.

Any source language [supported by Google Translate](https://cloud.google.com/translate/docs/languages)
is allowed, since auto-detection is used to translate text back to your desired language. The output language can be set via `config plugins.translateparty.language`, and defaults to English (`en`).

Samples:

```
<jlu5> %tp This text will be scrambled to near perfection.
<@Atlas> This message was standing almost completely.
```

```
<@Ere> %tp Mi ne scias la koloro de la hundo FK plugilo, cxar de tio, kio okazis en Islando
<@Atlas> My dick plows Aludra star name I do not know the color of cotton, Iceland
```

```
<jlu5> %tp An evil monster lurks beneath the forest.
<@Atlas> Error Evil Xasa woude.
```
