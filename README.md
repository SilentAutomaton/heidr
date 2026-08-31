# HEID//R

**For the Rationally Desperate.**

A modal terminal oracle. You ask a question, and the answer is *found* rather
than generated: it comes from radio noise, from an aircraft passing overhead,
from the last earthquake, from a page of the Library of Babel. A local language
model may interpret what was found, but it never chooses it.

Named after Heiðr, the völva of the *Völuspá*, who was burned three times and
born three times, and who travelled between farms telling people what was coming.

> Documentation: [English](docs/en/) · [Русский](docs/ru/)

## The rite has three slots

| Slot | What it does | Examples |
|---|---|---|
| Question | Turns your question into a key | `gematria`, `blind`, `planetary` |
| World | Fetches raw material from outside your control | `fm_voice`, `quake`, `babel` |
| Reading | Turns material into an answer | `iching`, `cutup`, `mute` |

Before each session a lottery draws one module per slot, so the ritual differs
every time and never settles into a habit. The lottery itself is seeded from the
world, not from a pseudo random generator.

## Status

Early. The package skeleton and configuration are in place; the interface and
the modules are being built step by step. See [docs/en/architecture.md](docs/en/architecture.md).

## Install

```
pip install -e .
heidr --splash
```

Optional extras: `pip install -e '.[audio,vosk,effects]'`

## Configure

```
cp config.example.toml ~/.config/heidr/config.toml
cp keymap.example.toml ~/.config/heidr/keymap.toml
```

API keys are read only from environment variables, never from the config file.
See `.env.example`.

## Credits

`HEID//R` borrows code and ideas from other people's work. Each module documents
its own sources; the full table lives in [docs/en/credits.md](docs/en/credits.md).

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
