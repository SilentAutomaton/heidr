# hline — world module

## What it does

Listens to the neutral hydrogen line at 1420.405751 MHz and reports how fast
whatever it caught is moving.

## Where the data comes from

The dongle through `rtl_power`, across two megahertz around the line.

This is the one module where "a signal from the universe" is not a metaphor.
Hydrogen is the most common substance there is, and it radiates at exactly this
frequency. Our galaxy was mapped with it.

## How it is processed

The scan gives a spectrum. The sky here is not a station with a sharp carrier
but a broad rise above the noise, so the baseline is the median of the whole
sweep and the signal is whatever stands out of it.

The peak's frequency then becomes a velocity. The arithmetic fits on one line: a
cloud moving away stretches the wave, so the line arrives below its rest
frequency. A hundred kilohertz of offset is twenty one kilometres per second.

The velocity and its excess over the noise become the material's text; the
offset in hertz, the velocity in metres per second and the excess in tenths of a
decibel become its numbers. `extra` carries a `detected` flag: below a one
decibel threshold the module says plainly that it caught noise.

## What this needs to work

A bare dongle with a whip will almost certainly return a flat spectrum, and the
module will show that. Real reception wants a low noise amplifier for 1420 MHz
and a directional antenna — a horn or a small dish.

Even then the line is not everywhere: you have to look into the plane of the
galaxy rather than in an arbitrary direction.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `span_hz` | 2000000 | Width of the sweep around the line |
| `step` | `10k` | Scan resolution |
| `seconds` | 30 | Integration time; longer is cleaner |
| `min_excess_db` | 1.0 | Below this it is noise |
| `gain` | empty | Empty means the receiver's automatic gain |

## Dependencies

A dongle, `rtl_power`, and an amplifier and antenna for 1420 MHz.

## Sources

The idea of receiving the hydrogen line on a consumer dongle comes from
[H-line-software](https://github.com/byggemandboesen/H-line-software) and
[rtlobs](https://github.com/evanmayer/rtlobs). No code was copied: the Doppler
formula and a median baseline need no borrowing.
