import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines

# The library: a wall of hexagons with letters falling through it. Shown while
# a page is being addressed, which is the only work the Library of Babel does.
ALPHABET = "abcdefghijklmnopqrstuvwxyz ,."
WALL = "/\\"
CELL_WIDTH = 6
CELL_HEIGHT = 3
FALLING = 0.25


class Hexlib(Painter):
    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.letters: dict[int, tuple[float, float]] = {}
        self.shape = (0, 0)
        self.last_tick = -1

    def sow(self, width: int, height: int) -> None:
        self.shape = (width, height)
        columns = self.rng.sample(range(width), k=max(1, int(width * FALLING)))
        self.letters = {
            column: (self.rng.uniform(-height, height), self.rng.uniform(0.2, 0.7))
            for column in columns
        }

    def advance(self, height: int) -> None:
        for column, (position, speed) in list(self.letters.items()):
            position += speed
            if position > height:
                position = -self.rng.uniform(0, height)
            self.letters[column] = (position, speed)

    def paint(self, frame: Frame) -> list[str]:
        if self.shape != (frame.width, frame.height):
            self.sow(frame.width, frame.height)
        elif frame.tick != self.last_tick:
            self.advance(frame.height)
        self.last_tick = frame.tick

        grid = blank(frame.width, frame.height)
        for y in range(frame.height):
            for x in range(frame.width):
                # A honeycomb drawn with nothing but two slashes.
                if (x + (y // CELL_HEIGHT) * CELL_WIDTH // 2) % CELL_WIDTH == 0:
                    grid[y][x] = WALL[(x + y) % 2]

        for column, (position, _speed) in self.letters.items():
            y = int(position)
            if 0 <= y < frame.height:
                grid[y][column] = ALPHABET[(column * 7 + y * 3) % len(ALPHABET)]
        return lines(grid)


@animation("hexlib", glyphs="ascii", fps=8)
class PlainHexlib(Hexlib):
    ramp = ASCII


@animation("hexlib", glyphs="blocks", fps=8)
class BlockHexlib(Hexlib):
    ramp = BLOCKS


@animation("hexlib", glyphs="braille", fps=8)
class BrailleHexlib(Hexlib):
    ramp = BRAILLE
