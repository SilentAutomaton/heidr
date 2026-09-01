import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, blank, lines, stamp

# Words falling out of order. Shown while the cut-up is being made, which is
# the one reading that takes the material apart rather than reading it.
WORDS = ("the", "roof", "night", "signal", "again", "answer", "wait", "listen", "noise")
DRIFT = 0.4


class Scissors(Painter):
    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.pieces: list[tuple[str, float, float, float]] = []
        self.shape = (0, 0)

    def sow(self, width: int, height: int) -> None:
        self.shape = (width, height)
        self.pieces = [
            (
                self.rng.choice(WORDS),
                self.rng.uniform(0, max(1, width - 8)),
                self.rng.uniform(-height, height),
                self.rng.uniform(0.15, DRIFT),
            )
            for _ in range(max(4, width // 8))
        ]

    def paint(self, frame: Frame) -> list[str]:
        if self.shape != (frame.width, frame.height):
            self.sow(frame.width, frame.height)

        grid = blank(frame.width, frame.height)
        for word, x, y, speed in self.pieces:
            place = (y + frame.tick * speed) % (frame.height + 2) - 1
            stamp(grid, [word], round(x), round(place))
        return lines(grid)


@animation("scissors", glyphs="ascii", fps=6)
class PlainScissors(Scissors):
    ramp = ASCII


@animation("scissors", glyphs="blocks", fps=6)
class BlockScissors(Scissors):
    ramp = BLOCKS
