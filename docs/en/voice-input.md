# Voice input

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/voice-input.md)

## What it is

A way to speak the question instead of typing it. Press `Ctrl-V` in insert mode,
talk, and the words appear in the input line as they are recognised.

## The only place the microphone is used

The microphone is used here and nowhere else in this program.

It does not record ambience, it is not an entropy source, it takes part in no
run, and it never turns itself on. The program listens to the air, not to the
room — and that is not a promise in the documentation but a property of the code:
`sounddevice.InputStream` is opened in exactly one place in the whole project,
`heidr/mic.py`.

The camera is not used anywhere, for anything.

## How it works

Blocks from the microphone go straight to whichever recogniser `[stt]` names. If
it can report partial results — and `vosk` can — the input line updates while you
are still speaking. If it only produces finished phrases, they arrive after a
pause.

Recording runs in a worker thread so the interface never blocks, and the line is
updated through `call_from_thread`. It listens for fifteen seconds by default.

After that everything is as with typing: `Enter` submits, `Esc` cancels. A
dictated question is no different from a typed one, including in that it cannot
be asked a second time.

## When no recogniser is configured

`Ctrl-V` answers: "Voice input needs a speech provider. Run :checkhealth to see
what is missing." Nothing happens, and typing keeps working.

The same holds if a recogniser is configured but `sounddevice` is not installed
or the system has no input device.

## Dependencies

A configured speech provider (see [stt.md](stt.md)) and `sounddevice`, installed
as the `audio` extra. Plus a working microphone.

## Sources

Nothing borrowed.
