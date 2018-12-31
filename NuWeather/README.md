## NuWeather

A weather plugin for Limnoria. It supports multiple backends:

- [Dark Sky](https://darksky.net) (default)
- [Apixu](https://www.apixu.com/)

For the Dark Sky backend, [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) is used to translate locations into latitude/longitude pairs.

### Quick start

1) Pick your preferred backend: `config help plugins.nuweather.defaultbackend`

2) Grab an API key. [Dark Sky](https://darksky.net/dev) | [Apixu](https://www.apixu.com/)

3) Configure it: `/msg yourbot config plugins.nuweather.apikeys.BACKENDNAME YOUR-API-KEY`

5) Set your default weather location: `setweather <your-preferred-location>`

6) Obtain weather: `weather [<optional location>]`
