# `:checkhealth`

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/checkhealth.md)

A command named and built after the neovim one: a single screen showing what
works, what does not, and what to do about it.

## Why it exists

This program has a lot of optional parts: the dongle, speech recognition, a
language model, a sound card, the network. Without any of them it keeps working,
only with fewer chains to pick from.

Which means "nothing is broken, that module simply did not come up" and "it is
broken" look identical from outside. `:checkhealth` is where the difference
becomes visible.

## What is checked

**Terminal.** Colour depth, glyph level, graphics protocol. A bare console is a
warning rather than an error: the program works there, only more plainly.

**Network.** Reachable or not. If not, the network sources are left out.

**Radio.** Whether an RTL-SDR device is present. On its own line, which of
`rtl_sdr`, `rtl_fm`, `rtl_power`, `rtl_433` and `dump1090` are installed.

**Stream tools.** Whether `ffmpeg`, `yt-dlp` and `kiwirecorder.py` are
installed. The sources that listen over the network run them.

**Audio.** Whether `sounddevice` is installed and an output device exists.

**Language model and speech.** Whether the provider could be built. If not, the
line says so and also says what stops working.

**Ledger.** How many entries, and whether the chain verifies. This is the only
check that can report `-` rather than `~`: a chain that does not verify means an
entry was edited by hand, and that cannot be passed over quietly.

**Slots.** How many modules in each slot are usable right now. An empty slot is
an error too: without one, no chain can be assembled.

## Reading it

Three marks at the start of a line.

`+` works. `~` does not work, but is not a fault: a capability is simply absent,
and the line says what goes with it. `-` is broken and needs fixing.

Plenty of warnings in ordinary use is normal. On a laptop with no dongle plugged
in it shows six `~` marks and stays entirely usable.

## Wording

Every line answers three questions in order: what happened, why, and what to do.
Not "SDR init failed" but "no RTL-SDR found. Plug in the dongle, then run
:checkhealth again."

That is not decoration. A status report is read at the moment something has
already stopped working, and an error code helps least of all right then.

## Sources

The name and the idea of one screen for the state of optional parts come from
neovim, where `:checkhealth` does exactly this. No code was taken: neovim is not
written in Python.
