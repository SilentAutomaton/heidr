# Speech providers

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/stt.md)

Speech recognition is used for exactly two things: dictating a question instead
of typing it, and turning captured radio into text. The microphone is used for
the first and nothing else.

## The contract

Every provider is one class with two methods:

```python
def available(self) -> bool
def transcribe(self, blocks: Iterable[np.ndarray]) -> Iterator[Partial]
```

A `Partial` carries text and a flag saying whether it is final. Providers that
can report a word before the sentence ends do so; providers that cannot yield
only final results.

## What ships

| `stt.provider` | Kind | Notes |
|---|---|---|
| `vosk` | streaming | Partial words appear while you are still speaking. Weaker on noisy shortwave, but right for dictation |
| `whisper_cpp` | window at a time | Nothing until the window closes, then a much better transcript. Right for radio |
| `api` | hosted | The OpenAI transcription shape, which other services copied |

`whisper_cpp` looks for `whisper-cli`, `whisper-cpp` or `main` on the path unless
`stt.binary` names one, and needs `stt.model_path` pointing at a `.bin` model.
`vosk` needs `stt.model_path` pointing at an unpacked model directory.

## Configuration

```toml
[stt]
provider = "vosk"
model_path = ""             # directory for vosk, .bin file for whisper.cpp
api_key_env = "HEIDR_STT_KEY"
window_s = 30               # whisper.cpp window length
language = "auto"
threads = 0                 # 0 lets whisper.cpp decide
```

As everywhere else, `api_key_env` is the name of an environment variable, never
the key.

## One source at a time

A sweep visits several stations, and every one of them is recognised on its own.
The blocks of a stop are kept in their own list and given to the provider in
their own call, so nothing is joined end to end. A single buffer of four
stations has three seams in it, and a model answers a seam by inventing a
sentence across it — whisper because its thirty second window straddles the
joint, vosk because one recogniser carries the last words of one station into
the first words of the next.

Recognition is the longest silent step in the program, so it counts itself off:
`transcribing 2/4` stands in the status line and in the panel, beside the mark
that turns.

## Which model for radio

For dictation almost anything works: you speak close to the microphone, clearly,
in a quiet room.

Radio is the opposite case, and the model size shows. The modules that listen
are [fm_voice](modules/fm_voice.md), [sw_voice](modules/sw_voice.md) and
[mw_voice](modules/mw_voice.md). On a short noisy fragment
`small` reports about half real words and half its own invention — plausible
Russian that was never broadcast. `medium` is noticeably better,
`large-v3-turbo` better still and roughly the same speed as `medium` thanks to
its reduced decoder.

A longer dwell helps as much as a bigger model. Fifteen to twenty seconds on one
station gives the model enough context to settle; five seconds does not.

Whether that invention is a defect depends on the module. For `fm_voice` it is —
there is clean speech to be had. For `sw_voice` it is the point: see that
module's document.

## A vosk model

whisper.cpp is built; vosk is installed and then given a model directory. The
models are published as zip archives at one address, and `stt.model_path` points
at the unpacked directory rather than at the archive:

```
curl -LO https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip -d ~/.local/share/heidr/models
```

| Model | Size | For |
|---|---|---|
| `vosk-model-small-en-us-0.15` | 40 MB | dictating in English |
| `vosk-model-small-ru-0.22` | 45 MB | dictating in Russian |
| `vosk-model-en-us-0.22` | 1.8 GB | English on a worse recording |

One model, one language. A small model is enough for dictation, which is what
vosk is here for; radio is whisper.cpp's work.

The [installer](binaries.md) does all of this for you, including the choice of
model. It also refuses to pair vosk with the released binary, which carries its
own Python and cannot load a package `pip` installed.

## When a provider cannot be used

A missing model, a missing binary or a missing key is checked at probe time, not
in the middle of a run. The `stt` capability is dropped, voice input says so,
the radio sources that need transcription are left out, and everything else
keeps working.

## Why whisper.cpp is built the way it is

The build is CPU only, `-march=native`, a pinned version, and no CUDA at all.
That is deliberately not the fastest arrangement available on this machine. The
trade is speed for durability: a driver update, a CUDA version change or an
ollama reinstall cannot break it, and a program that stops working after a system
upgrade is worse than a slow one.

## Building it

```
git clone --depth 1 --branch b4938 https://github.com/ggml-org/whisper.cpp
cd whisper.cpp
cmake -B build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
      -DGGML_NATIVE=ON -DGGML_CUDA=OFF -DGGML_VULKAN=OFF -DGGML_BLAS=OFF \
      -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_SERVER=OFF
cmake --build build -j"$(nproc)" --target whisper-cli
```

`BUILD_SHARED_LIBS=OFF` matters as much as the rest: the result is a three
megabyte executable that links nothing of its own, so it can be copied to
`/usr/local/bin` and forgotten about.

Then a model, and `stt.model_path` pointing at it:

```
curl -L -o ggml-large-v3-turbo-q5_0.bin \
  https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo-q5_0.bin
```

### What it costs

Measured on a six core i7-9750H with `ggml-large-v3-turbo-q5_0`, on eleven
seconds of clean speech:

| | Seconds |
|---|---|
| `-l en`, six threads | 26 |
| `-l auto`, six threads | 55 |
| `-l en`, twelve threads | 26 |

Two things follow. Twelve threads buy nothing on six physical cores, so
`stt.threads = 6`. And `language = "auto"` costs a second pass of the encoder,
which is the price of not mistranscribing a foreign station into the wrong
language — worth paying for radio, and the reason a thirty second window takes
a bit over a minute.

## Dependencies

`numpy`. The `vosk` package for the vosk provider, installed as the `vosk` extra.
A built `whisper.cpp` binary and a model file for that one. `requests` for the
hosted service.

## Sources

Nothing borrowed. [whisper.cpp](https://github.com/ggml-org/whisper.cpp) (MIT)
and [vosk-api](https://github.com/alphacep/vosk-api) (Apache-2.0) are used as
they are, not copied from.
