# Binaries and installers

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/binaries.md)

There are two ways in that do not need Python: a single binary you download and
run, and a script that downloads the binary and the outside programs with it.
Neither replaces the source install in [installing](install.md); they are the
short way for somebody who wants to try the program today.

Every release carries a binary for each system: Linux, Windows, and macOS on
both Intel and Apple silicon. The script fetches the binary everywhere, and on
Linux it installs the outside programs around it too.

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

**A signature.** No binary is signed. Windows SmartScreen and macOS Gatekeeper
will say so before the first run, and a binary downloaded through a browser
carries a quarantine mark on macOS: `xattr -d com.apple.quarantine heidr-macos-*`
takes it off.

**The outside programs on macOS.** The script brings the binary alone there.
The receiver, the speech recogniser and the rest are yours to install by hand;
the program says at every start which ones it found.

## The binary alone

The binaries are `heidr-linux-x86_64`, `heidr-windows-x86_64.exe`,
`heidr-macos-x86_64` and `heidr-macos-arm64`, with a `SHA256SUMS` beside them.
Linux, without the installer:

```
curl -fLO https://github.com/SilentAutomaton/heidr/releases/latest/download/heidr-linux-x86_64
chmod +x heidr-linux-x86_64
./heidr-linux-x86_64 --self-check
```

The same address with another file name brings the Windows or macOS binary;
on macOS, `chmod +x` after it.

The Linux binary runs on any distribution with glibc 2.31 or newer — Ubuntu
20.04, Debian 11, and everything since. It carries Python and every Python
dependency inside it and needs nothing installed.

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

Windows and macOS binaries are built where they run. PyInstaller packages the
interpreter and the prebuilt wheels of the architecture it runs under, so a
Windows binary needs Windows and a macOS binary needs a Mac; a cross-build is
not a thing it can do. The workflow in `.github/workflows/build-binaries.yml`
builds Linux, Windows and macOS on Apple silicon through GitHub Actions and
leaves the binaries in the run's artifacts — start it from the Actions tab with
the tag of the release to build. Intel macOS is the one target its free runners
do not carry, so that binary is built by hand on a Mac: a venv with
`pip install pyinstaller '.[audio,effects]'`, then `pyinstaller heidr.spec`,
exactly as the README describes for Linux.

## Checking

```
heidr --self-check
```

One line per capability, and for each missing one, the thing to install. How to
read the report is in [checking what works](checkhealth.md).
