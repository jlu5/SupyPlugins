# NuWeather

A weather plugin for Limnoria. It supports multiple weather and geocoding backends:

#### Weather Backends
- [Dark Sky](https://darksky.net) (default, API key required)
- [Apixu](https://www.apixu.com/) (API key required)

#### Geocoding Backends
- [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) (default, no API key required)
- [Google Maps](https://developers.google.com/maps/documentation/geocoding/start) (API key required)
- [OpenCage](https://opencagedata.com/) (API key required)

## Quick start

1) Pick your preferred weather backend: `config help plugins.NuWeather.defaultBackend`

2) Grab an API key. [Dark Sky](https://darksky.net/dev) | [Apixu](https://www.apixu.com/)

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

(If you're comfortable with re-creating your database from scratch, the other options tell NuWeather to save location by Supybot account (the default) or ident@host.)
