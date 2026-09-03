import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import row

# Rain on still water: a few drops, each sending a ring outward that fades as it
# goes. The same distance field the plasma is built from, with the sine taken
# along the radius instead of across the whole screen, which is a quarter of the
# arithmetic and a completely different picture.
#
# Where the drops fall is fixed rather than random. The field has to be the same
# on every repaint of one tick, and a still surface with four sources on it
# reads as water however the sources were chosen.
DROPS = ((0.24, 0.32, 0), (0.72, 0.26, 13), (0.42, 0.74, 26), (0.84, 0.66, 39))
WAVELENGTH = 10.0
SPEED = 2.6
PERIOD = 52
# How far behind the wavefront the ripple is still moving. Beyond this the water
# is flat again, which is what makes a ring read as a ring rather than as a mesh
# of standing waves.
TRAIN = 20.0
# The far half of a ring is worth seeing, so the whole field is lifted before it
# is biased back down; without this every ring sits on the faintest glyph.
GAIN = 1.7
QUIET = 1.3


def ripple(distance: float, age: float, spread: float) -> float:
    """One ring, seen `age` frames after the drop.

    The wave is a short train that travels outward, not a standing pattern
    filling the whole disc: it fades behind the front, and again with distance,
    so a late ring is a faint circle far out rather than a lit-up field.
    """
    lag = age * SPEED - distance
    if not 0 <= lag <= TRAIN:
        return 0.0
    behind = 1 - lag / TRAIN
    outward = max(0.0, 1 - distance / spread)
    return math.sin(lag * math.tau / WAVELENGTH) * behind * outward


def field(width: int, height: int, tick: int) -> list[list[float]]:
    spread = math.hypot(width, height * 2)
    rows = []
    for y in range(height):
        values = []
        for x in range(width):
            total = 0.0
            for across, down, delay in DROPS:
                # Rows are half as tall as they are wide, so the vertical
                # distance counts double or the rings come out as ovals.
                distance = math.hypot(x - width * across, (y - height * down) * 2)
                total += ripple(distance, (tick - delay) % PERIOD, spread)
            # Biased downward: this sits behind text that has to stay readable.
            values.append(min(1.0, abs(total) * GAIN) ** QUIET)
        rows.append(values)
    return rows


def paint(frame: Frame) -> list[str]:
    return [row(values, frame.ramp) for values in field(frame.width, frame.height, frame.tick)]


for level in ("ascii", "blocks", "braille"):
    animation("rings", glyphs=level, fps=10)(paint)
