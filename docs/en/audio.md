# Audio

## One way out

There is exactly one audio path through the program. Every sound — radio,
recordings, anything added later — goes through the same `Output` object and gets
the same treatment.

This is deliberate. "Every sound is levelled" could have been a rule written down
for whoever writes the next module, and hoped for. Instead a module has nowhere
to send audio that skips the levelling.

```
rtl_fm ──s16le──> to_float ──> Gain ──> limiter ──> sounddevice
                      ├──> spectrum ──> waterfall event
                      └──> ring buffer ──> speech provider
```

Samples are read once and fan out three ways. The waterfall's spectrum comes from
the same buffer as the sound, so the picture on screen and the sound in the
headphones are literally the same piece of radio.

## How levelling works

### Automatic gain

Each block's RMS gives the factor needed to reach the target. The gain does not
jump there; it moves toward it exponentially.

The speed differs by direction, and that matters. When the signal gets louder the
gain comes down within `attack_ms`, fifty milliseconds by default. When the
signal gets quieter the gain goes up over `release_ms`, four hundred.

The reason is pauses. There is always silence between words and between stations.
A fast release would haul that silence up to the target, so pauses would hiss at
full volume and the next word would hit like a hammer. A slow release means a
short pause stays a pause.

### The limiter

After the gain, the block's peak is measured. If it exceeds the ceiling, the
whole block is scaled so the peak sits exactly on it.

Scaled, not clipped. Clipping peaks means harmonics and a distinctive crackle;
scaling the block keeps the waveform's shape and simply makes it quieter for the
fraction of a second that needs it.

### Volume

Volume is applied after the gain and before the limiter. It is your control, not
the automation's: `-` and `+` move it in steps of five percent, `m` mutes, and
`:vol 40` sets an exact value. The current position shows in the status line.

The value is written straight back to the configuration, so the next session
starts where this one left off.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `volume` | 0.6 | Your control, zero to one |
| `target_rms` | 0.12 | The level the automation aims for |
| `limiter_ceiling` | 0.95 | Nothing leaves above this |
| `attack_ms` | 50 | How fast it comes down on loud |
| `release_ms` | 400 | How slowly it goes up on quiet |

All five change live and need no restart.

## Who owns the levels

The interface holds one `Levels` object, and the volume keys change that object
rather than a copy of the numbers. It travels into the rite on the context as
`ctx.levels`, and the sweep hands it to the `Output` it opens, so `-`, `+` and
`m` reach a station **while it is still playing** instead of at the next draw.

A module that plays sound takes the levels from the context and falls back to
the configuration when there is no interface:

```python
output = audio.Output(ctx.levels or audio.Levels.from_config(ctx.config), rate)
if ctx.has("audio"):
    output.open()
```

The stream is opened by whoever created it and closed in a `finally`, so a sweep
that fails halfway does not leave a device held open. `Output.open` is the line
that makes sound audible at all: without it the whole path still runs — levelled,
measured, transcribed — and reaches nobody. That is exactly what happened here
for a whole development cycle, and the test that opens a counting stand-in output
exists so it cannot happen twice.

## With no sound card

`sounddevice` is imported lazily, and if that fails `Output` keeps running dry:
blocks are processed, the spectrum is computed, the waterfall draws, and nothing
leaves. The oracle stays fully usable, just silent.

## Dependencies

`numpy` for the processing. `sounddevice` is optional and only needed for actual
output: `pip install 'heidr[audio]'`.

## Sources

Nothing borrowed. Fast attack, slow release, and a scaling limiter are ordinary
audio practice and have been for decades.
