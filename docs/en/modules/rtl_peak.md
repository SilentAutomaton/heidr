# rtl_peak — source

## What it does

Sweeps a band quickly, finds the strongest signal in it, and reports its
frequency.

## Where the data comes from

The dongle, through `rtl_power`, which makes one pass across the given band and
prints the power in each bin.

## How it is processed

`rtl_power` writes CSV: each line starts with a date, a time, the low and high
edges of a slice, the bin width and a sample count, then one power reading per
bin. The parser walks every line looking for the largest reading, skipping `nan`
where there were not enough samples.

The bin index, with the low edge and the step, gives the frequency. That becomes
the material's text; the frequency in hertz and the power in tenths of a decibel
become its numbers.

The module does not try to identify a station. It reports where the air is
loudest right now and leaves the reading to say what that means.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `band` | `88M:108M` | The band in `rtl_power` notation |
| `step` | `100k` | Bin width |
| `seconds` | 20 | How long the sweep takes |

## Dependencies

An RTL-SDR dongle plugged in, and `rtl_power` on the system.

## Sources

Nothing borrowed.
