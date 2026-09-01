import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE

# Conway's rules, 1970, and they are not ours to adjust: a live cell with two or
# three live neighbours lives on, a dead cell with exactly three is born, and
# everything else dies.
DENSITY = 0.32
STALE_AFTER = 3


def step(cells: set[tuple[int, int]], width: int, height: int) -> set[tuple[int, int]]:
    """One generation. The edges wrap, so nothing drifts off and vanishes."""
    counts: dict[tuple[int, int], int] = {}
    for x, y in cells:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx or dy:
                    neighbour = ((x + dx) % width, (y + dy) % height)
                    counts[neighbour] = counts.get(neighbour, 0) + 1

    return {
        cell
        for cell, count in counts.items()
        if count == 3 or (count == 2 and cell in cells)
    }


def soup(width: int, height: int, rng: random.Random, density: float = DENSITY) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(height)
        for x in range(width)
        if rng.random() < density
    }


class Life(Painter):
    """The oldest algorithmic animation there is, seeded by the world.

    When the board settles into a still life or a short oscillator it is sown
    again rather than left frozen: something has to keep moving.
    """

    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.cells: set[tuple[int, int]] = set()
        self.shape = (0, 0)
        self.recent: list[frozenset] = []
        self.last_tick = -1

    def reseed(self, width: int, height: int) -> None:
        self.shape = (width, height)
        self.cells = soup(width, height, self.rng)
        self.recent = []

    def advance(self, width: int, height: int) -> None:
        self.cells = step(self.cells, width, height)
        self.recent.append(frozenset(self.cells))
        self.recent = self.recent[-STALE_AFTER:]
        settled = len(self.recent) == STALE_AFTER and len(set(self.recent)) < STALE_AFTER
        if not self.cells or settled:
            self.reseed(width, height)

    def paint(self, frame: Frame) -> list[str]:
        if self.shape != (frame.width, frame.height):
            self.reseed(frame.width, frame.height)
        elif frame.tick != self.last_tick:
            self.advance(frame.width, frame.height)
        self.last_tick = frame.tick

        alive = self.ramp[-1]
        return [
            "".join(alive if (x, y) in self.cells else " " for x in range(frame.width))
            for y in range(frame.height)
        ]


@animation("life", glyphs="ascii", fps=6)
class PlainLife(Life):
    ramp = ASCII


@animation("life", glyphs="blocks", fps=6)
class BlockLife(Life):
    ramp = BLOCKS


@animation("life", glyphs="braille", fps=6)
class BrailleLife(Life):
    ramp = BRAILLE
