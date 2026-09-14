# Binaries and installers

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/binaries.md)

There are two ways in that do not need Python: a single binary you download and
run, and a script that downloads the binary and the outside programs with it.
Neither replaces the source install in [installing](install.md); they are the
short way for somebody who wants to try the program today.

The binary is Linux only so far. On Windows the script still installs everything
around the program, and the program itself comes from source.

## The installer

Linux:

```
curl -fLO https://raw.githubusercontent.com/SilentAutomaton/heidr/master/install.sh
sh install.sh
```

Windows, in PowerShell:

```
Invoke-WebRequest -Uri https://raw.githubusercontent.com/SilentAutomaton/heidr/master/install.ps1 -OutFile install.ps1
powershell -ExecutionPolicy Bypass -File install.ps1
```

The script asks what to install and installs nothing you did not name:

| | What it installs | From where |
|---|---|---|
| 1 | heidr | the latest release of this repository |
| 2 | the radio tools | the distribution's package manager |
| 3 | ffmpeg and yt-dlp | the package manager, and yt-dlp's own release |
| 4 | whisper.cpp and a model | its own release, and Hugging Face |
| 5 | vosk and a model | PyPI, and alphacephei.com |
| 6 | ollama and a model | the official install script |
| 7 | llama.cpp | its own release |

Only the first is needed. Everything else is a source of material or a way of
reading it, and the program says at every start which ones it found.

The last thing the installer does is write the settings for what it installed —
`stt.provider`, `stt.model_path`, `llm.provider` — and then run
`heidr --self-check`, so the last thing on screen is the program's own verdict
rather than the installer's.

Read the script before you run it. It is one file, it is short, and it is in
this repository.

## What it will not do

**The RTL-SDR on Windows.** Windows has no driver the `rtl_*` programs can use.
The installer says so and prints the WSL2 route instead of failing halfway.

**vosk with the binary.** vosk is a Python package that the program imports. The
released binary carries its own Python and cannot load anything `pip` installs,
so vosk needs a source install. whisper.cpp is a separate program the binary
runs, and works either way. The installer warns before it does anything.

**Windows, for now.** There is no Windows binary in the release, so on Windows
the script installs the outside programs and says that heidr itself has to come
from source. The reason is in *building them yourself* below.

**macOS.** Nothing is built for it, because nothing here can build it. macOS is
installed from source, as [installing](install.md) describes.

## The binary alone

Every release carries the Linux binary and `SHA256SUMS`. To use it without the
installer:

```
curl -fLO https://github.com/SilentAutomaton/heidr/releases/latest/download/heidr-linux-x86_64
chmod +x heidr-linux-x86_64
./heidr-linux-x86_64 --self-check
```

The Linux binary is built inside Debian bullseye, so it runs on any distribution
with glibc 2.31 or newer — Ubuntu 20.04, Debian 11, and everything since. It
carries Python and every Python dependency inside it and needs nothing
installed.

What it does not carry is the outside programs. `rtl_fm`, `ffmpeg`,
`whisper-cli` and ollama are run as subprocesses or reached over a socket, so
they are looked for on the path when the program starts, exactly as with an
ordinary install. A missing one removes the sources that need it and nothing
else. Sound is the one thing inside the binary that still needs a system
library: `sounddevice` looks for `libportaudio2`, and without it the oracle runs
silently.

## Settings from the command line

The installer configures the program through the same flag you can use yourself:

```
heidr --set stt.provider=whisper_cpp --set stt.model_path=~/.local/share/heidr/models/ggml-large-v3-turbo-q5_0.bin
```

Each `--set` takes one key and one value. The value is read as what it looks
like: `true` and `false` become switches, digits become numbers, everything else
stays text. A name the configuration does not hold is refused rather than
written. The same settings are editable inside the program with `:set`, which is
described in [settings and modules](settings-editor.md).

## Building them yourself

```
sh tools/build_release.sh
```

The Linux binary is built in `python:3.12-bullseye` through docker, from the
same `heidr.spec` the README documents. It is not built on the machine that
publishes it: a PyInstaller binary carries the C library it was linked against,
and one built on a rolling distribution runs on that distribution and nowhere
else. Debian bullseye is old enough to reach everything still in use.

The same script has a Windows target, under wine in `tobix/pywine`, and it does
not currently work: PyInstaller runs its collectors in subprocesses, and those
die under wine before the build begins. The script reports the failure and
carries on rather than pretending. A Windows binary needs a Windows machine, or
somebody who knows why those subprocesses die.

Pass `linux` or `windows` to build one of them. The result lands in `dist/` with
a `SHA256SUMS` beside it.

## Checking

```
heidr --self-check
```

One line per capability, and for each missing one, the thing to install. How to
read the report is in [checking what works](checkhealth.md).
