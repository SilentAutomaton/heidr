import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines

# A train of meshed gears, adapted from the Cog effect of asciimatics by Peter
# Brittain, Apache-2.0. https://github.com/peterbrittain/asciimatics
#
# The trick for one gear is a single parametric curve: the radius steps between
# two values every four units of the parameter, and the teeth appear on their
# own. The mechanism is that curve repeated along a line, with two rules taken
# from real gears — neighbours turn in opposite directions, and a small gear
# turns faster than the big one driving it.
POINTS = 81
STEP = math.pi / 40
TOOTH = 4
ASPECT = 2.0
RADII = (1.0, 0.62)
BASE_SPEED = 3.0


def tooth_radius(point: int, radius: float, depth: float) -> float:
    return radius - depth * (point // TOOTH % 2)


def train(width: int, height: int) -> list[tuple[float, float, float, int]]:
    """Where the gears sit, how big they are, and which way each turns."""
    biggest = max(2.0, (height - 1) / 2)
    gears: list[tuple[float, float, float, int]] = []
    centre_y = (height - 1) / 2

    x = 0.0
    index = 0
    while x < width + biggest * ASPECT:
        radius = biggest * RADII[index % len(RADII)]
        if index == 0:
            x = radius * ASPECT
        gears.append((x, centre_y, radius, 1 if index % 2 == 0 else -1))
        following = biggest * RADII[(index + 1) % len(RADII)]
        # Touching, so the teeth of one run into the teeth of the next.
        x += (radius + following) * ASPECT
        index += 1
    return gears


def draw_gear(grid, x: float, y: float, radius: float, turn: float, mark: str) -> None:
    previous = None
    for point in range(POINTS):
        angle = (turn + point) * STEP
        px = x + tooth_radius(point, radius, radius / 4) * ASPECT * math.sin(angle)
        py = y + tooth_radius(point, radius, radius / 4) * math.cos(angle)
        here = (round(px), round(py))
        if previous is not None:
            line(grid, previous[0], previous[1], here[0], here[1], mark)
        previous = here


class Cog(Painter):
    """The mechanism is turning. Shown while a language model is working.

    Not a progress bar: nothing here knows how far along the answer is. It says
    only that work is happening, which is the honest amount to say.
    """

    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        for x, y, radius, direction in train(frame.width, frame.height):
            # A small gear driven by a big one goes round faster, in proportion.
            turn = frame.tick * direction * BASE_SPEED / radius
            draw_gear(grid, x, y, radius, turn, self.ramp[-1])
        return lines(grid)


@animation("cog", glyphs="ascii", fps=12)
class PlainCog(Cog):
    ramp = ASCII


@animation("cog", glyphs="blocks", fps=12)
class BlockCog(Cog):
    ramp = BLOCKS


@animation("cog", glyphs="braille", fps=12)
class BrailleCog(Cog):
    ramp = BRAILLE
