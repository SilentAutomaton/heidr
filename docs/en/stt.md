# Speech providers

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
| `vosk` | genuinely streaming | Partial words appear while you are still speaking. Weaker on noisy shortwave, but right for dictation |
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

## Which model for radio

For dictation almost anything works: you speak close to the microphone, clearly,
in a quiet room.

Radio is the opposite case, and the model size shows. On a short noisy fragment
`small` reports about half real words and half its own invention — plausible
Russian that was never broadcast. `medium` is noticeably better,
`large-v3-turbo` better still and roughly the same speed as `medium` thanks to
its reduced decoder.

A longer dwell helps as much as a bigger model. Fifteen to twenty seconds on one
station gives the model enough context to settle; five seconds does not.

Whether that invention is a defect depends on the module. For `fm_voice` it is —
there is clean speech to be had. For `sw_voice` it is the point: see that
module's document.

## When a provider cannot be used

A missing model, a missing binary or a missing key is checked at probe time, not
in the middle of a rite. The `stt` capability is dropped, voice input says so,
the radio modules that need transcription leave the lottery, and everything else
keeps working.

## Why whisper.cpp is built the way it is

The build is CPU only, `-march=native`, a pinned version, and no CUDA at all.
That is deliberately not the fastest arrangement available on this machine. The
trade is speed for durability: a driver update, a CUDA version change or an
ollama reinstall cannot break it, and an oracle that stops working after a system
upgrade is not an oracle.

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
