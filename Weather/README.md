[![Build Status](https://travis-ci.org/GLolol/Supybot-Weather.svg?branch=master)](https://travis-ci.org/GLolol/Supybot-Weather)

# Limnoria plugin for Weather Underground (GLolol's fork)

## Introduction

I made this plugin because quite a few Weather plugins didn't work well and WunderWeather, which uses
this API, is on their older XML api that they don't have documented anymore and, one would assume, will
be deprecated at some point.

## Install

You will need a working Limnoria bot on Python 2.7/3.4 for this to work.

Go into your Limnoria plugin dir, usually `~/supybot/plugins` and run:

```
git clone https://github.com/GLolol/Supybot-Weather
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

or if you don't have or don't want to use root,

```
pip install -r requirements.txt --user
```


Next, load the plugin:

```
/msg bot load Weather
```

[Fetch an API key for Wunderground](http://www.wunderground.com/weather/api/) by signing up (free).
Once getting this key, you will need to set it on your bot before things will work.
Reload once you perform this operation to start using it.

```
/msg bot config plugins.Weather.apiKey <APIKEY>
```

Now, reload the bot and you should be good to go:

```
/msg bot reload Weather
```

*Optional:* There are some config variables that can be set for the bot. They mainly control output stuff.

```
/msg bot config search Weather
```

## Example Usage

```
<spline> @wunderground 10002
<myybot>  New York, NY :: Rain :: 52F | Visibility: 4.0mi | Saturday: Rain. High around 55F.  ...
```

## Features

There are a ton of options to configure. You can find these via:

```
/msg bot config search Weather
```

Many of these are also available via --help when calling the wunderground command.

Users can also have their location remembered by the plugin's internal database so that
they will not have to continually type in their location. NOTE: It uses their nick only,
so if they are on a different nick, even with an identical hostmask, it will not match.

You can use zipcodes (10002), cities (New York, NY), etc. Weather Underground is pretty
intelligent here.

```
<spline> @setweather 10002
<myybot> I have changed spline's weather ID to 10002
```

This now allows a user to type in the weather command w/o any arguments:

```
<spline> @wunderground
<myybot> Manchester, NH :: Rain :: 45F | Visibility: 10.0mi | Saturday: Occasional light rain. High 56F. ...
```

Users can also have the bot remember their preferred options, such as using Metric when displaying weather:

```
<spline> @setuser metric False
<myybot> I have changed spline's metric setting to 0
```
