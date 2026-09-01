# sky — world module

## What it does

Finds an aircraft that is over your head right now and hands you its callsign,
altitude and heading.

## Where the data comes from

The community ADS-B feed at adsb.lol, which aggregates transponder receptions
from volunteer ground stations:

```
https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{radius}
```

This is the network stand-in for `adsb_local`, which does the same job with your
own dongle and antenna. When the radio is plugged in, prefer that one: the
signal then really did come out of the sky and into your house.

## How it is processed

1. Your configured position and radius build the query.
2. The key's seed picks one aircraft out of the returned list.
3. The callsign becomes the text. If the aircraft is not broadcasting one, the
   registration is used; failing that, the transponder hex address.
4. Barometric altitude and track angle become the numbers.

Nothing is fetched until latitude and longitude are set. Until then the module
reports itself unavailable and stays out of the lottery, because an oracle
pointed at the sky above the Gulf of Guinea is not pointed at yours.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `latitude` | 0.0 | Your position. Must be set |
| `longitude` | 0.0 | Your position. Must be set |
| `radius_nm` | 50 | Search radius in nautical miles |
| `timeout` | 10 | Seconds to wait |

## Dependencies

`requests`. Network access. A configured position.

## Sources

Nothing was copied. The idea of an aircraft overhead as raw material is the one
behind [Skylight](https://github.com/cpaczek/skylight), which projects the same
data onto a ceiling instead.
