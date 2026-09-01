import math
import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines

# A drum recorder: the paper moves, the pen mostly rests, and now and then the
# ground moves. Shown while the earthquake feed is being read.
QUIET = 0.04
SHOCK_CHANCE = 0.03
DECAY = 0.86


class Seismo(Painter):
    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.trace: list[float] = []
        self.energy = 0.0
        self.last_tick = -1

    def advance(self, width: int) -> None:
        if self.rng.random() < SHOCK_CHANCE:
            self.energy = self.rng.uniform(0.5, 1.0)
        self.energy *= DECAY
        swing = self.rng.uniform(-1, 1) * (QUIET + self.energy)
        self.trace.append(swing)
        self.trace = self.trace[-width:]

    def paint(self, frame: Frame) -> list[str]:
        if not self.trace:
            # The paper already has a line on it before anything shakes.
            for _ in range(frame.width):
                self.advance(frame.width)
        elif frame.tick != self.last_tick:
            self.advance(frame.width)
        self.last_tick = frame.tick

        grid = blank(frame.width, frame.height)
        middle = (frame.height - 1) / 2
        start = frame.width - len(self.trace)
        previous = None
        for offset, swing in enumerate(self.trace):
            column = start + offset
            y = round(middle - swing * middle)
            y = max(0, min(frame.height - 1, y))
            if previous is not None:
                line(grid, column - 1, previous, column, y, self.ramp[-1])
            previous = y
        return lines(grid)


@animation("seismo", glyphs="ascii", fps=10)
class PlainSeismo(Seismo):
    ramp = ASCII


@animation("seismo", glyphs="blocks", fps=10)
class BlockSeismo(Seismo):
    ramp = BLOCKS


@animation("seismo", glyphs="braille", fps=10)
class BrailleSeismo(Seismo):
    ramp = BRAILLE
