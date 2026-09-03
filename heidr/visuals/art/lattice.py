import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import blank, lines

# A cloud of points settling onto one direction. Shown while the embed module is
# at work, which asks a model for the question as a vector and folds it into a
# number: many dimensions going in, one line coming out.
#
# Where the points start is arithmetic on their number rather than a generator,
# so the same tick paints the same screen however often it is repainted.
POINTS = 120
SETTLE = 34
HOLD = 12
ASPECT = 2.0


def scattered(number: int) -> tuple[float, float]:
    """A point of the cloud, spread by two turns that never line up."""
    angle = number * 2.399963
    radius = math.sqrt((number + 0.5) / POINTS)
    return radius * math.cos(angle), radius * math.sin(angle)


def paint(frame: Frame) -> list[str]:
    grid = blank(frame.width, frame.height)
    across, down = frame.width / 2, frame.height / 2
    reach = max(2.0, min(down - 1, frame.width / ASPECT / 2 - 1))
    # Out to the cloud, in to the line, and out again.
    phase = (frame.tick % (2 * SETTLE + 2 * HOLD)) - HOLD
    settled = min(1.0, max(0.0, phase / SETTLE)) if phase < SETTLE + HOLD else \
        min(1.0, max(0.0, (2 * SETTLE + HOLD - phase) / SETTLE))

    for number in range(POINTS):
        x, y = scattered(number)
        # The line every point is drawn toward is its own projection onto one
        # direction, which is what folding a vector down to a number does.
        along = (x + y) / 2
        x, y = x + (along - x) * settled, y + (along - y) * settled
        column = round(across + x * reach * ASPECT)
        row = round(down + y * reach)
        if 0 <= row < frame.height and 0 <= column < frame.width:
            grid[row][column] = frame.ramp[-1] if settled > 0.8 else frame.ramp[len(frame.ramp) // 2]
    return lines(grid)


for level in ("ascii", "blocks", "braille"):
    animation("lattice", glyphs=level, fps=12)(paint)
