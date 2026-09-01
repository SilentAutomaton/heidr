import math
import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines

# A sweep going round, and a contact that fades after the beam has passed it.
# Shown while the sky is being asked what is overhead.
ASPECT = 2.0
CONTACTS = 3
FADE = 12


class Radar(Painter):
    ramp = ASCII

    def __init__(self):
        self.rng = random.Random()
        self.contacts: list[tuple[float, float]] = []
        self.shape = (0, 0)

    def sow(self, width: int, height: int) -> None:
        self.shape = (width, height)
        self.contacts = [
            (self.rng.uniform(0, math.tau), self.rng.uniform(0.3, 0.95)) for _ in range(CONTACTS)
        ]

    def paint(self, frame: Frame) -> list[str]:
        if self.shape != (frame.width, frame.height):
            self.sow(frame.width, frame.height)

        grid = blank(frame.width, frame.height)
        across, down = frame.width / 2, frame.height / 2
        radius = max(2.0, min(down - 0.5, frame.width / ASPECT / 2 - 0.5))
        beam = frame.tick * 0.25 % math.tau

        line(
            grid,
            round(across),
            round(down),
            round(across + radius * ASPECT * math.sin(beam)),
            round(down - radius * math.cos(beam)),
            self.ramp[-1],
        )

        for angle, distance in self.contacts:
            # Bright just after the beam passes, then fading until it comes
            # round again.
            since = (beam - angle) % math.tau
            level = max(0.0, 1 - since * FADE / math.tau)
            if level <= 0:
                continue
            x = round(across + radius * distance * ASPECT * math.sin(angle))
            y = round(down - radius * distance * math.cos(angle))
            if 0 <= y < frame.height and 0 <= x < frame.width:
                grid[y][x] = self.ramp[max(1, round(level * (len(self.ramp) - 1)))]
        return lines(grid)


@animation("radar", glyphs="ascii", fps=12)
class PlainRadar(Radar):
    ramp = ASCII


@animation("radar", glyphs="blocks", fps=12)
class BlockRadar(Radar):
    ramp = BLOCKS


@animation("radar", glyphs="braille", fps=12)
class BrailleRadar(Radar):
    ramp = BRAILLE
