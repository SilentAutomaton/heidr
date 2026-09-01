# sdr_noise — world module

## What it does

Listens to an empty frequency and hands the rite the noise itself — not a
signal, but what is left when there is no signal.

## Where the data comes from

An RTL-SDR dongle through `rtl_sdr`, tuned to a frequency nobody transmits on.
What arrives is the receiver's own thermal noise, atmospheric interference, and
distant background.

## How it is processed

Raw samples cannot be trusted as they are: they carry a bias, and the computer's
own electronics leak into them. So the stream first goes through Von Neumann
debiasing — bit pairs `01` give a zero, `10` give a one, and equal pairs are
discarded — which removes any constant bias whatever its cause.

The discarded pairs are not wasted. They are hashed with SHA-512 and the digest
is mixed back into the accepted stream; there was entropy in them, and throwing
it away would be careless.

The cleaned stream is then hashed, and the first thirty-two bytes of the digest
become the material's numbers. This material has no text. Noise says nothing; it
only supplies a number.

`extra` records how many bytes arrived and how many survived debiasing. The
ratio is roughly one in four, and it shows how even the stream was.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `frequency` | 88000000 | An empty frequency in hertz |
| `seconds` | 3.0 | How long to record |

Pick your own frequency: what is empty in one city is occupied in another.

## Dependencies

An RTL-SDR dongle plugged in, and `rtl_sdr` on the system.

## Sources

The chain of Von Neumann debiasing followed by SHA-512 whitening from the
discarded pairs comes from [rtl-entropy](https://github.com/pwarren/rtl-entropy)
by Paul Warren, GPL-3.0. Its warning travels with it: atmospheric sampling picks
up interference, and the antenna is better shielded.
