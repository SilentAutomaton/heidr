import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines

# A turning cog, adapted from the Cog effect of asciimatics by Peter Brittain,
# Apache-2.0. https://github.com/peterbrittain/asciimatics
#
# The trick is one parametric curve: the radius steps between two values every
# four units of the parameter, and the teeth appear on their own.
POINTS = 81
STEP = math.pi / 40
TOOTH = 4
ASPECT = 2.0


def tooth_radius(point: int, radius: float, depth: float) -> float:
    return radius - depth * (point // TOOTH % 2)


def cog(width: int, height: int, turn: float, mark: str, direction: int = 1) -> list[list[str]]:
    grid = blank(width, height)
    radius = max(2.0, min(height / 2 - 1, width / ASPECT / 2 - 1))
    across, down = width / 2, height / 2

    previous = None
    for point in range(POINTS):
        angle = (turn * direction + point) * STEP
        x = across + tooth_radius(point, radius, radius / 4) * ASPECT * math.sin(angle)
        y = down + tooth_radius(point, radius, radius / 4) * math.cos(angle)
        here = (round(x), round(y))
        if previous is not None:
            line(grid, previous[0], previous[1], here[0], here[1], mark)
        previous = here
    return grid


class Cog(Painter):
    """Something is turning. Shown while a language model is working.

    Not a progress bar: nothing here knows how far along the answer is. It says
    only that work is happening, which is the honest amount to say.
    """

    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        return lines(cog(frame.width, frame.height, frame.tick, self.ramp[-1]))


@animation("cog", glyphs="ascii", fps=12)
class PlainCog(Cog):
    ramp = ASCII


@animation("cog", glyphs="blocks", fps=12)
class BlockCog(Cog):
    ramp = BLOCKS


@animation("cog", glyphs="braille", fps=12)
class BrailleCog(Cog):
    ramp = BRAILLE
