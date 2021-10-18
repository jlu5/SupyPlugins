This is a [bird-lg-go](https://github.com/xddxdd/bird-lg-go/) API client for Limnoria.

## Configure

First configure the following variables:

- `plugins.birdlggo.lgserver` - point this to your looking glass server (e.g. `http://lg.highdef.dn42/`)
- `plugins.birdlggo.nodes` - a space separated list of nodes to query. These should use internal server names (as shown in request URLs to the frontend), not the display names that the frontend shows in the navigation bar.

## Usage

Currently this provides a slimmed down UI for traceroute and BIRD's `show route`:

### Show route

This will only show the first / preferred route, with an AS path for BGP routes.

```
21:58 <@jlu5> @showroute 172.20.66.67
21:58 <atlas> 172.20.229.114 -> 172.20.66.67: unicast via 192.168.88.113 on igp-us-chi01 [Type: BGP univ] [Pref: 100/165] [AS path: 76190 4242420101]
21:58 <atlas> 172.20.229.113 -> 172.20.66.67: unicast via 192.168.88.123 on igp-us-nyc02 [Type: BGP univ] [Pref: 100/108] [AS path: 4242422601 4242420101]
21:58 <atlas> 172.20.229.117 -> 172.20.66.67: unicast via 172.23.235.1 on dn42fsn-tbspace [Type: BGP univ] [Pref: 100] [AS path: 76190 4242420101]
```

### Traceroute

```
22:02 <@jlu5> @traceroute wiki.dn42
22:02 <atlas> 172.20.229.114 -> wiki.dn42: 33.310 ms | 172.20.229.122 172.20.129.165 169.254.64.2 169.254.64.2 172.23.0.80
22:02 <atlas> 172.20.229.113 -> wiki.dn42: 29.169 ms | 172.20.229.123 172.20.129.167 169.254.64.2 169.254.64.2 172.23.0.80
22:02 <atlas> 172.20.229.117 -> wiki.dn42: 4.907 ms | 172.20.129.169 169.254.64.2 169.254.64.2 172.23.0.80
```
