# sw_voice — world module

## What it does

The same as `fm_voice`, but on shortwave in AM: slower, noisier, and far less
intelligible.

## Where the data comes from

The dongle through `rtl_fm` in AM mode, from the broadcast segment around
3.9–4.0 MHz. Reception here depends on the time of day, the state of the
ionosphere, and whatever antenna is on your windowsill.

## How it is processed

The mechanics are exactly those of [fm_voice](fm_voice.md): a route across
frequencies, a dwell on each, one buffer feeding sound, spectrum and recogniser,
then the anchor filter.

Only the numbers differ. The default sweep is `bounce`, the dwell is six seconds
rather than four, and the band is narrow.

## Why this is a separate module

Not because of the settings, but because of what is audible.

On FM the recogniser does its job: there is clean speech and it transcribes it.
On shortwave there is almost no clean speech. There is fading, there are distant
stations in unfamiliar languages, there are unmodulated carriers, and there is
noise. The recogniser produces words anyway — it is obliged to produce
something — and those words are half its own invention.

This is the electronic voice phenomenon, reproduced honestly and with no
mystification: a person hears speech in noise, a machine hears speech in noise,
and both fail in recognisably the same way.

The material from here comes out strange. That is the intent.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `band` | `3.9-4.0` | The band in megahertz |
| `sweep` | `bounce` | `forward`, `backward`, `bounce`, `random` |
| `stops` | 6 | How many frequencies to visit |
| `dwell_s` | 6 | Seconds on each |
| `mode` | `am` | Demodulation for `rtl_fm` |
| `rate` | 16000 | Sample rate |
| `bins` | 64 | Bars in the spectrum |

Receiving shortwave on a cheap dongle needs either an upconverter or a direct
sampling receiver. Without one the module will hear only noise — which is, after
all, still material.

## Dependencies

The same as `fm_voice`: a dongle, `rtl_fm`, and a configured speech provider.

## Sources

The same as [fm_voice](fm_voice.md): sweep modes from
[gqrx-ghostbox](https://github.com/DougHaber/gqrx-ghostbox), ISC licensed.
