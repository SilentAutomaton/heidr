# apt — world module

## What it does

Records a NOAA weather satellite pass and decodes it into a picture of the
clouds above you.

## Where the data comes from

The dongle through `rtl_fm`, on the frequency of one of the three remaining
satellites:

| Satellite | Frequency |
|---|---|
| NOAA-15 | 137.620 MHz |
| NOAA-18 | 137.9125 MHz |
| NOAA-19 | 137.100 MHz |

They transmit in the clear, unencrypted, as weather satellites have since 1960.
Anyone can receive them.

## How it is processed

The module records ordinary audio — the picture is encoded inside it, amplitude
modulated onto a subcarrier. The resulting WAV goes to `noaa-apt`, which turns
it into a PNG. The image is kept, and its path becomes the material's text.

## What this module does not do

It does not predict passes.

Orbital prediction needs fresh TLE elements and the SGP4 algorithm, which is a
library and a project of its own. So the run has to be started while the
satellite is actually above the horizon — take the time from any pass predictor.

If no satellite was there, `noaa-apt` finds no picture in the recording, the
module says so plainly, and the question comes back unspent.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `satellite` | `noaa-19` | `noaa-15`, `noaa-18` or `noaa-19` |
| `seconds` | 600 | Recording length; a pass lasts about twelve minutes |
| `keep_in` | `~/.local/share/heidr/apt` | Where the images go |
| `gain` | empty | Empty means the receiver's automatic gain |

## Dependencies

A dongle, a circularly polarised antenna for 137 MHz, `rtl_fm`, and
[noaa-apt](https://github.com/martinber/noaa-apt) (GPL-3.0) installed. Without
it the module is left out of the choice.

## Sources

All decoding is done by Martin Bernardi's `noaa-apt`, run as a separate program.
Its licence does not reach this code.
