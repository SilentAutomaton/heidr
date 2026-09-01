import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE

# Stars at three depths drifting at three speeds. Parallax is the whole trick:
# the near ones move, the far ones barely do, and the eye reads distance.
DEPTHS = (0.25, 0.55, 1.0)
DENSITY = 0.04


class Starfield(Painter):
    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.stars: list[tuple[float, int, float]] = []
        self.shape = (0, 0)

    def sow(self, width: int, height: int) -> None:
        self.shape = (width, height)
        count = max(1, int(width * height * DENSITY))
        self.stars = [
            (self.rng.uniform(0, width), self.rng.randrange(max(1, height)), self.rng.choice(DEPTHS))
            for _ in range(count)
        ]

    def paint(self, frame: Frame) -> list[str]:
        if self.shape != (frame.width, frame.height):
            self.sow(frame.width, frame.height)

        grid = [[" "] * frame.width for _ in range(frame.height)]
        for x, y, depth in self.stars:
            column = int(x - frame.tick * depth * 0.5) % frame.width
            if 0 <= y < frame.height:
                grid[y][column] = self.ramp[max(1, round(depth * (len(self.ramp) - 1)))]
        return ["".join(line) for line in grid]


@animation("starfield", glyphs="ascii", fps=8)
class PlainStarfield(Starfield):
    ramp = ASCII


@animation("starfield", glyphs="blocks", fps=8)
class BlockStarfield(Starfield):
    ramp = BLOCKS


@animation("starfield", glyphs="braille", fps=8)
class BrailleStarfield(Starfield):
    ramp = BRAILLE
