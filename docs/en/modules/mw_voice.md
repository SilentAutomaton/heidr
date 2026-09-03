# mw_voice — source

## What it does

Listens to medium wave — the AM band broadcasting started on, and which is still
alive in much of the world.

## Where the data comes from

The dongle through `rtl_fm` in AM mode, across 531–1602 kHz. Channels sit on a
nine kilohertz grid in Europe, Asia and Africa, and a ten kilohertz one in the
Americas.

At night something happens here that never happens on FM: the ionosphere lifts,
absorption falls, and a station a thousand kilometres away arrives louder than
the local one. By day the same receiver on the same antenna hears almost
nothing.

So medium wave is the one band in this project where the hour changes not the
quality of reception but what there is to catch at all.

## Direct sampling

As on shortwave, the tuner cannot reach down here: `rtl_fm` gets `-E direct2`
and `rtl_power` gets `-D`. A receiver with that support and a long antenna are
needed — a loop is better, being markedly quieter against the household
interference that medium wave is full of.

## How it is processed

As in [sw_voice](sw_voice.md): a scan, a route across the carriers found, twenty
seconds on each, one buffer feeding sound, spectrum and recogniser.

What differs is the scan step — nine kilohertz, matching the channel grid — and
the same figure as the minimum spacing between stations, so adjacent channels do
not merge into one.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `band` | `0.531-1.602` | The medium wave band in megahertz |
| `stops` | 3 | How many stations to visit |
| `dwell_s` | 20 | Seconds on each |
| `direct` | `direct2` | Direct sampling branch |
| `scan_step` | `9k` | The channel grid; `10k` in the Americas |
| `scan_separation` | 9000 | Minimum spacing between stations |

## Dependencies

A dongle with direct sampling, an antenna for medium wave, `rtl_fm`,
`rtl_power`, and a configured speech provider.

## Sources

Nothing borrowed. The machinery is shared with [sw_voice](sw_voice.md).
