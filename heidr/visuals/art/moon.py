import math
import time

from heidr.question.moment import SYNODIC_DAYS, moon_age
from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE

# A terminal cell is about twice as tall as it is wide, so the disc is drawn
# twice as wide in columns as it is in rows. Otherwise the moon is an egg.
ASPECT = 2.0
DAYS_PER_TICK = 0.25


def lit(x: float, y: float, radius: float, angle: float) -> bool:
    """Is this point on the disc in sunlight?

    The terminator is an ellipse whose width is the cosine of the phase angle,
    which is the whole of the geometry. Waxing lights the right, waning the
    left.
    """
    half = math.sqrt(max(radius * radius - y * y, 0.0))
    edge = math.cos(angle) * half
    if math.sin(angle) >= 0:
        return x >= edge
    return x <= -edge


def disc(width: int, height: int, angle: float, ramp: str) -> list[str]:
    radius = max(1.0, min(height / 2 - 0.5, width / ASPECT / 2 - 0.5))
    bright, dim = ramp[-1], ramp[max(1, len(ramp) // 4)]

    rows = []
    for line in range(height):
        y = line - (height - 1) / 2
        cells = []
        for column in range(width):
            x = (column - (width - 1) / 2) / ASPECT
            if x * x + y * y > radius * radius:
                cells.append(" ")
            else:
                cells.append(bright if lit(x, y, radius, angle) else dim)
        rows.append("".join(cells))
    return rows


class Moon(Painter):
    """Tonight's phase, and then the month running on from it."""

    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        days = moon_age(time.time()) + frame.tick * DAYS_PER_TICK
        angle = math.tau * (days % SYNODIC_DAYS) / SYNODIC_DAYS
        return disc(frame.width, frame.height, angle, self.ramp)


@animation("moon", glyphs="ascii", fps=4)
class PlainMoon(Moon):
    ramp = ASCII


@animation("moon", glyphs="blocks", fps=4)
class BlockMoon(Moon):
    ramp = BLOCKS


@animation("moon", glyphs="braille", fps=4)
class BrailleMoon(Moon):
    ramp = BRAILLE
