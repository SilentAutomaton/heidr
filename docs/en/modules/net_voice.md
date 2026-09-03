# net_voice — source

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/net_voice.md)

## What it does

Visits several internet radio stations picked at random, keeps a few seconds of
each, plays them out loud and transcribes them. It is `fm_voice` for a machine
with no radio in it.

## Where the data comes from

The [Radio Browser](https://api.radio-browser.info/) directory, which lists
around fifty-eight thousand stations and needs no key of any kind. The audio
comes from the stations themselves, over ordinary HTTP.

The directory answers on several mirrors and which of them is alive changes, so
the request goes to `all.api.radio-browser.info` and the name resolves to one
that is. The caller names itself in the `User-Agent`, which is the one thing the
service asks of anybody using it.

## How it is processed

### Choosing the stations

One query asks for a pool of stations in random order, already filtered to those
the directory checked and found working. About one in eleven listed stations is
flagged broken, and around one in thirteen of the rest still fails to answer, so
the pool is larger than the number of stops: twenty offered for four wanted.

The key's seed then fixes the order the pool is walked in. The directory
shuffles, but the route a question takes has to come from the question, or the
same question would go somewhere else every time.

### One buffer, three consumers

`ffmpeg` reads one station and writes sixteen kilohertz mono audio, which is
exactly what the recogniser wants and needs no conversion. One command covers
MP3, AAC, Ogg, Opus and HLS alike.

Each block goes three ways on the same turn of the loop: to the speaker, to the
spectrum for the waterfall, and to the buffer for the recogniser. Nothing is
collected first and played afterwards. What you hear is what is on screen is
what becomes the text.

A station sends a burst of buffered audio the moment a listener connects, so the
first seconds arrive faster than real time. They are not thrown away and they
are not slowed down: the sound card blocks until it has room, and the loop keeps
its pace from the speaker. On a machine with no sound card the whole visit is
simply quicker, because nobody is listening to it.

### When a station does not answer

It is passed over and the next one is tried. A directory entry that was working
this morning is a normal thing to find dead, which is why the pool is
over-filled. Only if every station in the pool is silent does the module refuse.

### Transcription and anchors

The gathered audio is handed to the speech provider, and finished phrases become
the material. If the question module produced anchors, phrases carrying those
words are kept — unless none do, in which case everything is kept.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `stops` | 4 | How many stations to reach |
| `dwell_s` | 5 | Seconds on each |
| `pool` | 20 | How many stations to ask the directory for |
| `rate` | 16000 | Sample rate |
| `bins` | 64 | Bars in the spectrum |
| `codec` | `MP3` | Stream format to ask for; empty accepts any |
| `bitrate_min` | 64 | Below this the recogniser has little to work with |
| `language` | — | A language name, as the directory spells it |
| `tag` | — | A directory tag. `news` or `talk` finds speech rather than music |

Four stations of five seconds is under half a minute, and often much less.

## Dependencies

A working network, `ffmpeg` on the path, and a configured speech provider.
Missing any of the three keeps the module out of the choice. A sound card is
optional: without one everything works silently.

Capabilities: `net`, [`stt`](../stt.md).

## Sources

The directory is [Radio Browser](https://api.radio-browser.info/). Its
maintainer places the collected data in the public domain; the station streams
themselves stay the property of whoever broadcasts them, and nothing here is
stored — the audio is transcribed in memory and dropped.

Resolving the host through `all.api.radio-browser.info` and naming the caller in
the `User-Agent` are the conventions of
[pyradios](https://github.com/andreztz/pyradios) by André P. Santos, MIT. No
code was copied. Asking the directory for more stations than are needed, and
passing over the ones that will not answer, is the practice of
[pyradio](https://github.com/coderholic/pyradio) by Ben Dowling, MIT.

The idea of visiting several transmitters in turn and letting the dwell time
decide what is caught comes from
[gqrx-ghostbox](https://github.com/DougHaber/gqrx-ghostbox) by Douglas Haber,
BSD-3-Clause, as it does for the radio sources.
