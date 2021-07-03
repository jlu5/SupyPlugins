# Qalculate! plugin for Limnoria

This plugin provides a `calc` command using [Qalculate!](https://qalculate.github.io/), a multi-purpose desktop calculator.

More specifically, it is a thin wrapper around Qalculate!'s CLI interface `qalc`.

## Requirements

You can download Qalculate! from https://qalculate.github.io/downloads.html

## Examples

```
<jlu5> `calc 12+34*56
<bitmonster> 12 + (34 * 56) = 1916

<jlu5> `calc log(2048) / log(2)
<bitmonster> log(2048, e) / log(2, e) = approx. 11

<jlu5> `calc 20 kg to lb
<bitmonster> 20 * kilogram = approx. 44 lb + 1.479239 oz

<jlu5> `calc 50 USD to CAD
<bitmonster> 50 * dollar = approx. CAD 65.982418

<jlu5> `calc solve(x^2-10x+9=0)
<bitmonster> solve(((x^2) - (10 * x) + 9) = 0, x) = [9, 1]
```

