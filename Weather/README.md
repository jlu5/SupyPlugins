[![Build Status](https://travis-ci.org/GLolol/Supybot-Weather.svg?branch=master)](https://travis-ci.org/GLolol/Supybot-Weather)

# Limnoria plugin for Weather Underground (GLolol's fork)

## Installation

You will need a working Limnoria bot on Python 2.7/3.2+ for this to work.

1) Go into your Limnoria plugin dir, usually `~/supybot/plugins` and run:

```
git clone https://github.com/GLolol/Supybot-Weather
```

Alternatively, you can fetch this plugin (albeit a slightly older version) via Limnoria's PluginDownloader using: `install GLolol Weather`.

2) Load the plugin:

```
/msg bot load Weather
```

3) [Fetch an API key from Wunderground](http://www.wunderground.com/weather/api/) by signing up (free).
Once getting this key, you will need to set it on your bot before things will work.


```
/msg <yourbot> config plugins.Weather.apiKey <APIKEY>
```

4) *Optional:* There are some config variables that can be set for the bot. They mainly control output stuff.

```
/msg bot config search Weather
```

## Example Usage

When calling the `wunderground` command, you can use zip codes (10002), cities (New York, NY), etc. Weather Underground is pretty
intelligent here.

```
<spline> @wunderground 10002
<myybot>  New York, NY :: Rain :: 52F | Visibility: 4.0mi | Saturday: Rain. High around 55F...
```

## Features

There are a ton of options to configure. You can find these via:

```
/msg bot config search Weather
```

Users can also have their location remembered by the plugin's internal database so that
they will not have to continually type in their location.

```
<spline> @setweather 10002
<myybot> I have changed spline's weather ID to 10002
```

This now allows a user to type in the weather command w/o any arguments:

```
<spline> @wunderground
<myybot> Manchester, NH :: Rain :: 45F | Visibility: 10.0mi | Saturday: Occasional light rain. High 56F. ...
```

Users can also have the bot remember their preferred options, such as using metric units when displaying weather:

```
<spline> @setuser metric False
<myybot> I have changed spline's metric setting to 0
```
