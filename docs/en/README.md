# Documentation

[HEID//R](../../README.md) · [Русский](../ru/README.md)

Everything here has a Russian mirror under `docs/ru/` with the same file name.

## Using it

| Document | What is in it |
|---|---|
| [Installing](install.md) | Linux, macOS, Windows, and the one file build |
| [Keys](keys.md) | The whole key map, what it borrows from vim, and where the two disagree |
| [Settings and modules](settings-editor.md) | The two lists inside the program, and `:set` |
| [Checking what works](checkhealth.md) | What `:checkhealth` reports and how to read it |
| [Input history](history.md) | Past questions and commands, kept apart |
| [Voice input](voice-input.md) | Dictating a question instead of typing it |

## How it works

| Document | What is in it |
|---|---|
| [Architecture](architecture.md) | The three slots, the contracts, the ledger, and what happens when a module cannot answer |
| [Animations](animations.md) | Painters, the glyph ladder, the panel, the window title |
| [Audio](audio.md) | One output path, levelling, and who owns the volume |
| [Language models](llm.md) | Providers, sampling options, and how the reading is asked for |
| [Speech](stt.md) | vosk, whisper.cpp, the hosted shape, and which model to use for radio |
| [Credits](credits.md) | Every borrowing, with its author and its licence |

## Working on it

| Document | What is in it |
|---|---|
| [Adding a module](module-guide.md) | One file, one decorator, one function |
| [Code style](codestyle.md) | What the code is allowed to look like |
| [Testing](testing.md) | What is tested, what is not, and why |
| [The wordmark](../brand/README.md) | Colours, files, and how to rebuild it |

## Modules

Thirty-three of them, one document each, in [modules/](modules/). The tables in the
[project README](../../README.md#modules) list them with what they need.

**Question modules** turn the question into a key:
[gematria](modules/gematria.md) ·
[skeleton](modules/skeleton.md) ·
[acrostic](modules/acrostic.md) ·
[rarest](modules/rarest.md) ·
[blind](modules/blind.md) ·
[moment](modules/moment.md) ·
[calendar](modules/calendar.md) ·
[planetary](modules/planetary.md) ·
[reversal](modules/reversal.md) ·
[embed](modules/embed.md)

**Sources** find the material:
[mojibake](modules/mojibake.md) ·
[babel](modules/babel.md) ·
[quake](modules/quake.md) ·
[chain](modules/chain.md) ·
[sky](modules/sky.md) ·
[sdr_noise](modules/sdr_noise.md) ·
[rtl_peak](modules/rtl_peak.md) ·
[ism](modules/ism.md) ·
[adsb_local](modules/adsb_local.md) ·
[hline](modules/hline.md) ·
[apt](modules/apt.md) ·
[fm_voice](modules/fm_voice.md) ·
[sw_voice](modules/sw_voice.md) ·
[mw_voice](modules/mw_voice.md) ·
[net_voice](modules/net_voice.md) ·
[kiwi_voice](modules/kiwi_voice.md) ·
[twitch_voice](modules/twitch_voice.md)

**Readings** turn the material into an answer:
[cutup](modules/cutup.md) ·
[oblique](modules/oblique.md) ·
[iching](modules/iching.md) ·
[tarot](modules/tarot.md) ·
[mute](modules/mute.md) ·
[pythia](modules/pythia.md)
