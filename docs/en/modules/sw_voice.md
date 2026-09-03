# sw_voice — source

## What it does

Listens to shortwave broadcasting in AM: draws one of the metre bands, scans it,
finds carriers, and dwells on them for twenty seconds each, transcribing what it
hears.

## Where the data comes from

An RTL-SDR dongle through `rtl_fm` in AM mode. One band is drawn per sweep from
five:

| Band | Megahertz | When it is alive |
|---|---|---|
| 49 m | 5.85–6.20 | Most reliable after dark |
| 41 m | 7.20–7.45 | Evening and night |
| 31 m | 9.40–9.90 | The workhorse, audible almost always |
| 25 m | 11.60–12.10 | Daytime |
| 19 m | 15.10–15.80 | Daytime, long paths |

This is not decoration. Shortwave reflects off the ionosphere, and the
ionosphere changes by the hour: what roars on 49 metres at midnight is simply
absent there at noon. The module does not try to guess which band is open — it
draws one and sees what is there.

## Direct sampling

The R820T tuner and its relatives cannot reach below about 24 MHz. So shortwave
arrives by sampling the input directly rather than through the tuner: `rtl_fm`
gets `-E direct2` and the `rtl_power` scan gets `-D`.

Two conditions follow, and without them the module will hear only noise.

A receiver that supports it. The RTL-SDR Blog V4 has an HF input built in, but
wants that vendor's driver. On an ordinary dongle direct sampling needs an
adapter or a board modification.

And an antenna. The ten centimetre whip that suffices for FM receives nothing on
a six metre wavelength. Several metres of wire is the minimum, a tuned antenna
better.

## How it is processed

The rest is as in [fm_voice](fm_voice.md): a scan, a route across the carriers
found, a dwell on each, one buffer feeding sound, spectrum and recogniser, then
the anchor filter.

The numbers differ. The scan step is five kilohertz rather than a hundred —
shortwave channels sit close together. The margin above the noise floor is six
decibels rather than eight, because a distant station has no business being
loud. The dwell is twenty seconds rather than fifteen: the signal fades in and
out, and five seconds can land squarely in a null.

## What is audible here

Not what is on FM, which is the whole reason this is a separate module.

There is almost no clean speech. There is fading, there are stations in
languages you do not know, there are unmodulated carriers, and there is noise.
The recogniser produces words anyway — it is obliged to produce something — and
a good share of them are its own invention.

This is the electronic voice phenomenon, reproduced honestly and with no
mystification: a person hears speech in noise, a machine hears speech in noise,
and both fail in recognisably the same way. The material from here comes out
strange, and that is the intent.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `band` | five metre bands | A list; the draw takes one |
| `stops` | 3 | How many stations to visit |
| `dwell_s` | 20 | Seconds on each |
| `direct` | `direct2` | Direct sampling branch, `direct` or `direct2` |
| `scan_step` | `5k` | Scan resolution |
| `scan_margin` | 6.0 | Decibels above the floor to count as a station |
| `scan_separation` | 10000 | Minimum spacing between stations |
| `gain` | empty | Empty means the receiver's own automatic gain |

## Dependencies

A dongle that receives shortwave, an antenna for it, `rtl_fm`, `rtl_power`, and
a configured speech provider. A larger model earns its keep here in particular:
on a noisy fragment `small` invents about half of what it reports.

## Sources

Sweep modes from [gqrx-ghostbox](https://github.com/DougHaber/gqrx-ghostbox) by
Doug Haber, ISC licensed. The direct sampling flags are documented in `rtl_fm`
and `rtl_power`'s own help.
