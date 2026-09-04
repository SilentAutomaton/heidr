# Installing

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/install.md)

Python 3.11 or newer. Everything past that is optional and the program says so
at startup: `heidr --self-check` lists what works on this machine and what is
missing.

## Linux

```
pip install -e '.[audio]'
heidr
```

For the receiver, install `rtl-sdr` from the package manager: it brings
`rtl_sdr`, `rtl_fm` and `rtl_power`, which the radio sources run as
subprocesses. `rtl_433` and `dump1090` are separate packages and only two
sources need them.

For speech, either `pip install -e '.[vosk]'` or a build of
[whisper.cpp](https://github.com/ggml-org/whisper.cpp); see
[stt.md](stt.md), which has the exact build line.

For a language model, ollama or a llama.cpp server on localhost. Neither is
required: five of the six readings need no model at all, and only `pythia` does.

## macOS

Native. Nothing needs emulating, and the terminal that ships with the system is
enough, though iTerm2 or kitty draw the braille animations better.

```
brew install rtl-sdr ollama
pip install -e '.[audio]'
```

`sounddevice` finds CoreAudio without help. whisper.cpp builds the same way as
on Linux and uses the Accelerate framework, so it is faster there than the
figures in [stt.md](stt.md) suggest.

## Windows

Everything except the receiver works natively.

```
py -m pip install -e ".[audio]"
py -m heidr
```

Two conditions. Use Windows Terminal rather than the old console host: the old
one draws neither the block glyphs nor the colours. And run it from a shell that
leaves the escape sequences alone, which PowerShell and cmd inside Windows
Terminal both do.

What works: the interface, the animations, sound through `sounddevice`, a local
model through the Windows build of ollama, and copying with `y`, which Windows
Terminal supports. Paths like `~/.config/heidr` land in the user profile by
themselves. `/etc/heidr` does not exist there, and its absence is not an error:
that layer is simply skipped.

What does not: the RTL-SDR. Windows has no driver the `rtl_*` programs can use
the way Linux does. The way through is WSL2 plus
[usbipd-win](https://github.com/dorssel/usbipd-win), which forwards the USB
device into the Linux side:

```
winget install usbipd
usbipd list
usbipd bind --busid <the dongle's id>
usbipd attach --wsl --busid <the dongle's id>
```

Inside WSL2 the receiver is then an ordinary Linux device, and the Linux
instructions apply unchanged.

## One file, no install

`heidr.spec` builds a single executable with Python and every dependency inside
it. See the README for the three commands. The external programs stay external
even then: `rtl_fm`, `whisper-cli` and ollama are looked for on the path at run
time, and a missing one only removes the sources that need it.

## Checking

```
heidr --self-check
```

How to read the report is in [checking what works](checkhealth.md).
One line per capability, and for each missing one, the thing to install. A
machine with nothing but Python still runs the program: `gematria//babel//iching`
needs no network, no radio and no model.
