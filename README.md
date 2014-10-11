[![Build Status](https://travis-ci.org/reticulatingspline/Weather.svg?branch=master)](https://travis-ci.org/reticulatingspline/Weather)

# Limnoria plugin for Weather Underground

## Introduction

I made this plugin because quite a few Weather plugins didn't work well and WunderWeather, which uses
this API, is on their older XML api that they don't have documented anymore and, one would assume, will
be depreciated at some point.

## Install

You will need a working Limnoria bot on Python 2.7 for this to work.

Go into your Limnoria plugin dir, usually ~/supybot/plugins and run:

```
git clone https://github.com/reticulatingspline/Weather
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

Next, load the plugin:

```
/msg bot load Weather
```

[Fetch an API key for Wunderground](http://www.wunderground.com/weather/api/) by signing up (free).
Once getting this key, you will need to set it on your bot before things will work.
Reload once you perform this operation to start using it.

```
/msg bot config plugins.Weather.apiKey APIKEY
```

Now, reload the bot and you should be good to go:

```
/msg bot reload Weather
```

Optional: There are some config variables that can be set for the bot. They mainly control output stuff.

```
/msg bot config search Weather
```

## Example Usage

```
<spline> @wunderground 10002
<myybot>  New York, NY :: Rain :: 52F | Visibility: 4.0mi | Saturday: Rain. High around 55F.  ...
```

## Features

There are a ton of options to configure. You can look through these via

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
@setweather 10002 
```

This now allows a user to type in the weather command w/o any arguments:

```
<spline> @wunderground
<myybot> Manchester, NH :: Rain :: 45F | Visibility: 10.0mi | Saturday: Occasional light rain. High 56F. ...
```

Users can also have the bot remember their options like for using Metric when displaying weather:

```
<spline> @setuser metric False
```

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via Amazon or browse my [wish list](http://amzn.com/w/380JKXY7P5IKE).

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.