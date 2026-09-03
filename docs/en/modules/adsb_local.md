# adsb_local — source

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/adsb_local.md)

## What it does

Takes an aircraft passing overhead right now — but unlike the `sky` module, it
receives that aircraft on your own antenna rather than asking someone else's
server.

## Where the data comes from

A `dump1090` already running nearby, which serves what it receives in
BaseStation format on port 30003. `dump1090` owns the dongle while it runs, so it
has to be started separately and in advance.

The difference from `sky` is not technical but a matter of meaning. Here the
signal really did come out of the sky to your home, instead of travelling through
someone else's receiver and someone else's server.

## How it is processed

BaseStation is built so that each message carries one thing: the callsign in one,
the altitude in another, the track in a third. So the parser does not read lines
individually — it folds them together by the transponder's hex address, filling
in each aircraft's card as the messages arrive.

The key's seed picks one finished card. The callsign becomes the text, or the
transponder address if the aircraft does not broadcast one. Altitude and track
become the numbers.

An empty sky is not an error. Over a small town at night you may catch nothing,
and then the material comes back empty.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `host` | `127.0.0.1` | Where `dump1090` is listening |
| `port` | 30003 | The BaseStation port |
| `seconds` | 45 | How long to collect messages |

## Dependencies

An RTL-SDR dongle plugged in and `dump1090` running. The module checks the port
and is left out of the choice when nothing answers.

Capabilities: [`sdr`](../install.md).

## Sources

Nothing borrowed. [dump1090](https://github.com/antirez/dump1090), ISC licensed,
runs as a separate program.
