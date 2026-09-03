# twitch_voice — source

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/twitch_voice.md)

## What it does

Listens to a live Twitch channel picked at random for a few seconds, plays it
and transcribes it. People talking to a camera, unaware of the question, which
is the same thing the radio sources are after.

## Where the data comes from

Twitch's own interface for developers, called Helix. It reports which channels
are broadcasting at this moment; `yt-dlp` turns a channel into a playlist URL,
and `ffmpeg` reads the audio from there.

This is the one module in the program that needs an account. Helix grants
nothing anonymously: every request carries an application identifier and a
token, and the token is issued against a secret. Register an application at
`dev.twitch.tv`, then put its two values in the environment:

```
HEIDR_TWITCH_ID=
HEIDR_TWITCH_SECRET=
```

Either one missing keeps the module out of the choice. Neither is ever read from
the configuration file, and neither is ever written to the ledger.

### What is being leaned on

Say it plainly. Helix is the interface Twitch offers for finding out who is
broadcasting, and asking it is the sanctioned thing to do. Reading the audio
with `yt-dlp` is not: Twitch's terms of service ask that their site be reached
by a person with a browser. This module is off unless you supply your own
credentials, and using it is your decision about your own account.

Nothing is stored. The audio is transcribed in memory and dropped; no recording,
no file, and the material keeps only the channel names and what was said.

## How it is processed

### Choosing a channel

One request lists channels that are live, in the configured language. The key's
seed fixes the order they are visited in, so a question takes the route the
question decides.

A channel is resolved to a playlist only when the rite actually reaches it. Two
stops out of a listing of twenty means two resolutions, not twenty: a channel
nobody hears costs nothing.

### Listening

`ffmpeg` reads the playlist and writes sixteen kilohertz mono audio. Each block
goes three ways on the same turn of the loop — the speaker, the spectrum for the
waterfall, the buffer for the recogniser — so what is heard, what is drawn and
what becomes text are the same moment.

A channel that stopped broadcasting between the listing and now resolves to
nothing, and is passed over for the next one.

### Transcription and anchors

As for the other voice sources: finished phrases become the material, and the
phrases carrying the question's anchors are kept unless none do.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `stops` | 2 | How many channels to hear |
| `dwell_s` | 5 | Seconds on each |
| `pool` | 20 | How many live channels to list |
| `language` | `en` | Two-letter code, as Twitch spells it. Empty accepts any |
| `rate` | 16000 | Sample rate |
| `bins` | 64 | Bars in the spectrum |

Two channels is about ten seconds, most of it spent resolving playlists.

## Dependencies

A working network, a configured speech provider, `ffmpeg` and `yt-dlp` on the
path, and both environment variables set. Missing any of them keeps the module
out of the choice.

Capabilities: `net`, [`stt`](../stt.md).

## Sources

The listing is Twitch's [Helix API](https://dev.twitch.tv/docs/api/). Its terms
are Twitch's, and the section above says which of them this module leans on.

[yt-dlp](https://github.com/yt-dlp/yt-dlp) is released into the public domain
under the Unlicense, and is run as a separate program. `ffmpeg` likewise.

YouTube was tried and rejected. Finding a live stream needs an API key whose
free quota allows about a hundred draws a day in total, and the extraction step
did not answer at all in testing — YouTube now demands a proof-of-origin token
and refuses clients that cannot produce one. A module that fails most of the
time is worse than no module.
