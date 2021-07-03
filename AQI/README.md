# World Air Quality Index plugin for Limnoria

This plugin retrieves [air quality index](https://en.wikipedia.org/wiki/Air_quality_index) info from the World Air Quality Index project ([aqicn.org](https://aqicn.org)).

## Setup

1) Get an API key: https://aqicn.org/api

2) Configure the API key: `config plugins.aqi.apikey <your-api-token>`

## Usage

```
<@jlu5> `aqi Vancouver
<%bitmonster> Vancouver International Airport #2, British Comlumbia, Canada ::  7 (Good)  <https://aqicn.org/city/british-comlumbia/vancouver-international-airport--2>; from British Columbia, Canada Air Quality Monitoring Agency and World Air Quality Index Project
```

## Extended Geolookup

The [built-in city search](https://aqicn.org/json-api/doc/#api-City_Feed-GetCityFeed) provided by aqicn.org is fairly limited, so this plugin also supports using geocoding backends from the [NuWeather](../NuWeather) plugin (when it is loaded and configured).

You can set the default geocoding backend via the `plugins.aqi.geocodeBackend` option, or override it per call using the `--geocode-backend` command option. By default, the backend is set to "native", which refers to aqicn.org's built-in search.
