import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE

# Falling columns of glyphs, in the register cmatrix has kept in terminals for
# twenty years. https://github.com/abishekvashok/cmatrix
#
# Quieter than the film: this sits behind text that has to stay readable.
GLYPHS = "01234567890abcdefghijklmnopqrstuvwxyz$#*+=-<>|/\\"
COLUMNS_IN_USE = 0.4


class Rain(Painter):
    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.drops: dict[int, tuple[float, float, int]] = {}
        self.shape = (0, 0)
        self.last_tick = -1

    def sow(self, width: int, height: int) -> None:
        self.shape = (width, height)
        columns = self.rng.sample(range(width), k=max(1, int(width * COLUMNS_IN_USE)))
        self.drops = {
            column: (self.rng.uniform(-height, 0), self.rng.uniform(0.3, 1.2), self.rng.randrange(9999))
            for column in columns
        }

    def advance(self, height: int) -> None:
        for column, (position, speed, seed) in list(self.drops.items()):
            position += speed
            if position - self.tail(height) > height:
                position = -self.rng.uniform(0, height / 2)
                speed = self.rng.uniform(0.3, 1.2)
            self.drops[column] = (position, speed, seed)

    def tail(self, height: int) -> int:
        return max(3, height // 2)

    def paint(self, frame: Frame) -> list[str]:
        if self.shape != (frame.width, frame.height):
            self.sow(frame.width, frame.height)
        elif frame.tick != self.last_tick:
            self.advance(frame.height)
        self.last_tick = frame.tick

        grid = [[" "] * frame.width for _ in range(frame.height)]
        tail = self.tail(frame.height)
        for column, (position, _speed, seed) in self.drops.items():
            for age in range(tail):
                y = int(position) - age
                if not 0 <= y < frame.height:
                    continue
                # The head is a letter, the tail fades along the ramp.
                if age == 0:
                    grid[y][column] = GLYPHS[(seed + y) % len(GLYPHS)]
                else:
                    level = 1 - age / tail
                    grid[y][column] = self.ramp[max(1, round(level * (len(self.ramp) - 1)))]
        return ["".join(line) for line in grid]


@animation("rain", glyphs="ascii", fps=10)
class PlainRain(Rain):
    ramp = ASCII


@animation("rain", glyphs="blocks", fps=10)
class BlockRain(Rain):
    ramp = BLOCKS


@animation("rain", glyphs="braille", fps=10)
class BrailleRain(Rain):
    ramp = BRAILLE
