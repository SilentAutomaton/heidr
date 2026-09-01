# ism — world module

## What it does

Listens to the domestic radio hum around the house: the neighbours' weather
stations, tyre pressure sensors, doorbells, fridge thermometers.

## Where the data comes from

The dongle, through `rtl_433`, on 433.92 MHz — the unlicensed band where cheap
domestic electronics talk to each other in the clear, with no encryption at all.

## How it is processed

`rtl_433` prints one line of JSON per message received. The parser keeps only
whole lines: reception is ragged, and half a line is ordinary rather than an
error.

From each message it takes the device model and the fields that mean something to
a person — temperature, humidity, pressure, wind speed, battery state — and
builds the material's text from them. Device identifiers become its numbers.

The material comes out funny and very concrete: `Nexus-TH: temperature_C 18.4,
humidity 62`. None of these devices know your question, which is the whole point.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `frequency` | `433.92M` | 915 MHz is more common in America |
| `seconds` | 45 | How long to listen |

## Dependencies

An RTL-SDR dongle plugged in, and `rtl_433` on the system.

## Sources

Nothing borrowed. [rtl_433](https://github.com/merbanan/rtl_433), GPL-2.0, is
run as a separate program.
