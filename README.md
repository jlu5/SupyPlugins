[![Build Status](https://travis-ci.org/GLolol/Supybot-Weather.svg?branch=master)](https://travis-ci.org/GLolol/Supybot-Weather)
# Limnoria plugin for Weather Underground

## Installation

You will need a working Limnoria bot on Python 2.7/3.2+ for this to work.

1) Go into your Limnoria plugin dir (usually `~/limnoria/plugins`), and run:

```
git clone https://github.com/GLolol/Supybot-Weather Weather
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

## Example Usage

When calling the `weather` command, you can use zip codes (10002), cities (New York, NY), etc. Weather Underground is pretty
intelligent here.

```
<GLolol> @weather 10002
<Atlas> New York, NY :: Rain :: 52F | Visibility: 4.0mi | Saturday: Rain. High around 55F...
```

## Features

There are a ton of options to configure. You can find these via:

```
/msg bot config search Weather
```

Users can also have their location remembered by the plugin's internal database so that
they will not have to continually type in their location.

```
<GLolol> @setweather 10002
<Atlas> Done.
```

This now allows a user to type in the weather command w/o any arguments:

```
<GLolol> @weather
<Atlas> New York, NY :: Clear :: 64F/17C | Wind: N@7kph | Thursday: Clear. Low 14C. Thursday Night: A clear sky. Low 14C. Winds SSE at 10 to 15 km/h.
```

Users can also have the bot remember their preferred options, such as using metric units when displaying weather:

```
<GLolol> @setuser metric False
<Atlas> Done.
```
