# Limnoria plugin for Weather Underground

## Installation

1) Download the plugin, either via Git or Limnoria's PluginDownloader (`install GLolol Weather`).

2) Load the plugin:

```
/msg bot load Weather
```

3) [Fetch an API key from Wunderground](http://www.wunderground.com/weather/api/) by signing up (free).
Once you get this key, you will need to set it up on your bot:

```
/msg <yourbot> config plugins.Weather.apiKey <APIKEY>
```

## Example Usage

When calling the `weather` command, you can provide location in many forms, including city names (e.g. Vancouver), ZIP codes (e.g. 10002), "city, country" pairs (e.g. "Sydney, Australia", and [ICAO airport codes](https://en.wikipedia.org/wiki/International_Civil_Aviation_Organization_airport_code) (e.g. KJFK)


```
<GLolol> @weather 10002
<Atlas> New York, NY :: Mostly Cloudy :: 55F/12C (Humidity: 53%) | Monday: Mostly cloudy. Low 11C. Monday Night: Cloudy. Slight chance of a rain shower. Low 11C. Winds ENE at 10 to 15 km/h.
```

Users can also have their location remembered by the bot so that they don't have to continually type in their location.

```
<GLolol> @setweather 10002
<Atlas> Done.
```

This allows a user to use the `weather` command without any arguments:

```
<GLolol> @weather
<Atlas> New York, NY :: Clear :: 64F/17C | Wind: N@7kph | Thursday: Clear. Low 14C. Thursday Night: A clear sky. Low 14C. Winds SSE at 10 to 15 km/h.
```

Users can also have the bot remember their preferred options, such as using metric units when displaying forecasts:

```
<GLolol> @setuser metric True
<Atlas> Done.
```
