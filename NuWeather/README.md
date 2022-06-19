# NuWeather

A weather plugin for Limnoria. It supports multiple weather and geocoding backends:

#### Weather Backends
- [OpenWeatherMap](https://openweathermap.org/) (default, API key required)
- [WWIS](https://worldweather.wmo.int/) (**no** API key required, major cities only)
- [weatherstack](https://weatherstack.com/) (current conditions only, API key required)
- [Dark Sky](https://darksky.net) (**DEPRECATED**: API key required; new signups closed)

#### Geocoding Backends
- [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) (default, no API key required)
- [Google Maps](https://developers.google.com/maps/documentation/geocoding/start) (API key required)
- [OpenCage](https://opencagedata.com/) (API key required)

## Quick start

1) Pick your preferred weather backend: `config help plugins.NuWeather.defaultBackend`

2) Grab an API key. [OpenWeatherMap](https://openweathermap.org/appid) | [weatherstack](https://weatherstack.com/) | ~~[Dark Sky](https://darksky.net/dev)~~ (new signups no longer accepted)

    - WWIS is another option that requires no API key, but is limited (in most countries) to major cities

3) Configure it: `/msg yourbot config plugins.NuWeather.apikeys.BACKENDNAME YOUR-API-KEY`

4) Set your default weather location: `setweather <your-preferred-location>`

5) Obtain weather: `weather [<optional location>]`

## Migrating from the Weather plugin

This plugin includes a script to migrate from the [Weather](../Weather) plugin's SQLite DB to NuWeather's binary format.

```
$ ./weather-migrate.py -h
usage: weather-migrate [-h] infile outfile

Migrates user locations from the Weather plugin to NuWeather.

positional arguments:
  infile      input filename (BOT_DATA_DIR/Weather.db)
  outfile     output filename (e.g. BOT_DATA_DIR/NuWeather.db)

optional arguments:
  -h, --help  show this help message and exit
```

### Migration instructions

1) If you have not loaded NuWeather previously, **load** the plugin for the first time so that config entries are populated.

2) Then, **unload** the plugin before running the migration script. You may also wish to make a backup of your current `NuWeather.db` if it is of any use.

3) Run the script on the right files: `./weather-migrate.py BOT_DATA_DIR/Weather.db BOT_DATA_DIR/NuWeather.db`

4) After performing the migration, set the **`plugins.NuWeather.DBAddressingMode`** option to **`nicks`** (since the previous database tracks locations by nick):

```
config plugins.NuWeather.DBAddressingMode nicks
```

5) Load the plugin again for these changes to take effect.

(If you're comfortable with re-creating your database from scratch, the other options tell NuWeather to save location by Limnoria account (the default) or ident@host.)

## Location lookup (Geocoding) backends

* weatherstack provides weather lookup by place name directly, and does not need further configuration.
* OpenStreetMap, WWIS, and Dark Sky backends use a separate service to translate place names into GPS coordinates, a process known as **geocoding**.

The default geocoding backend is [OpenStreetMap's Nominatim](https://nominatim.openstreetmap.org/); this can be configured via the `plugins.NuWeather.geocodeBackend` option.

Other options include [Google Maps](https://developers.google.com/maps/documentation/geocoding/start) and [OpenCage](https://opencagedata.com/).
These may provide more relevant results for North America (e.g. US ZIP codes), but both require API keys:

- [Google Maps](https://developers.google.com/maps/documentation/geocoding/get-api-key) (requires credit card billing) | [OpenCage](https://opencagedata.com/api)

API keys for geocoding backends are similarly configured as `plugins.NuWeather.apikeys.BACKENDNAME`.
