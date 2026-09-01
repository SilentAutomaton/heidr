import math
import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import row

# Shown when nothing is being captured. It is not a progress bar and does not
# claim to mean anything: it exists so the oracle looks awake rather than hung.
#
# Wavelengths with no common multiple, so the pattern never tiles into
# something that looks like a bug.
STRETCHES = (0.0731, 0.1279, 0.2113)
QUIET = 2.2
SEED = 1


def field(width: int, height: int, phase: float, seed: int = SEED) -> list[list[float]]:
    rng = random.Random(seed)
    offsets = [rng.uniform(0, math.tau) for _ in range(len(STRETCHES))]
    rows = []
    for line in range(height):
        values = []
        for column in range(width):
            value = sum(
                math.sin(column * stretch + line * stretch * 3.7 + phase * (index + 1) / 2 + offset)
                for index, (stretch, offset) in enumerate(zip(STRETCHES, offsets))
            )
            # Bias the whole field downward: this is something to glance past,
            # not to read.
            values.append(((value / len(STRETCHES) + 1) / 2) ** QUIET)
        rows.append(values)
    return rows


def paint(frame: Frame) -> list[str]:
    phase = frame.tick * 0.15
    return [row(values, frame.ramp) for values in field(frame.width, frame.height, phase)]


for level in ("ascii", "blocks", "braille"):
    animation("drift", glyphs=level, fps=6)(paint)
