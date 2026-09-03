# fm_voice — source

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/fm_voice.md)

## What it does

Sweeps the FM broadcast band, stopping on each frequency for a few seconds,
plays what is there out loud, and transcribes it.

## Where the data comes from

An RTL-SDR dongle through `rtl_fm`, from ordinary 88–108 MHz radio. This is the
one module you can listen to.

## How it is processed

### The sweep

First a route is planned: which frequencies to visit, in which order. There are
four modes, taken from `gqrx-ghostbox`.

`forward` climbs, `backward` descends, `bounce` reaches the top edge and comes
back, `random` scatters across the band. The key's seed fixes the order, so the
same question would take the same route.

The dwell time matters more than the mode. It decides whether you catch a
fragment of a sentence or nothing but noise. Fifteen seconds by default: shorter
than that and the recogniser gets a scrap it has to invent half of.

### One buffer, three consumers

Samples are read once and fan out three ways at the same moment: to the audio
output, where they are levelled; to the spectrum for the waterfall; and to a
buffer for the recogniser.

Which gives a pleasant property: the picture on screen, the sound in the
headphones and the text underneath are literally the same piece of radio at the
same instant.

### Transcription and anchors

The gathered audio is decimated to sixteen kilohertz and handed to the speech
provider. Finished phrases become the material's text.

If the question module produced anchors, phrases containing those words are kept.
But if nothing matches, everything is kept: staying silent because the air did
not happen to say your word would be cheating in the other direction.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `band` | `88.0-108.0` | The band in megahertz |
| `sweep` | `random` | `forward`, `backward`, `bounce`, `random` |
| `stops` | 4 | How many stations to visit |
| `dwell_s` | 15 | Seconds on each |
| `mode` | `wbfm` | Demodulation for `rtl_fm` |
| `rate` | 32000 | Sample rate |
| `bins` | 64 | Bars in the spectrum |

Four stops of fifteen seconds is about a minute including the scan and
retuning.

## Dependencies

An RTL-SDR dongle plugged in, `rtl_fm` on the system, and a configured speech
provider. Missing any of the three keeps the module out of the choice. A sound
card is optional: without one everything works silently.

Capabilities: [`sdr`](../install.md), [`stt`](../stt.md).

## Sources

The four sweep modes, and the idea of making dwell time the setting that matters,
come from [gqrx-ghostbox](https://github.com/DougHaber/gqrx-ghostbox) by
Douglas Haber, BSD-3-Clause.
