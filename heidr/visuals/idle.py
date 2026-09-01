import math
import random

from heidr.registry import visual
from heidr.visuals.base import ASCII, BLOCKS, BRAILLE, Visualisation, row

# Shown when nothing is being captured. It is not a progress bar and does not
# claim to mean anything: it exists so the oracle looks awake rather than hung.


def field(width: int, height: int, phase: float, seed: int) -> list[list[float]]:
    """A slow drifting interference pattern, the same every time for a seed."""
    rng = random.Random(seed)
    offsets = [rng.uniform(0, math.tau) for _ in range(3)]
    rows = []
    for line in range(height):
        values = []
        for column in range(width):
            value = 0.0
            for index, offset in enumerate(offsets):
                stretch = (index + 2) / 7
                value += math.sin(column * stretch + line * stretch / 2 + phase + offset)
            values.append((value / len(offsets) + 1) / 2)
        rows.append(values)
    return rows


class Idle(Visualisation):
    ramp = ASCII
    seed = 1

    def on_mount(self) -> None:
        self.phase = 0.0
        self.set_interval(0.2, self.step)

    def step(self) -> None:
        self.phase += 0.15
        self.refresh()

    def feed(self, payload) -> None:
        # A tick carries nothing; the animation runs on its own clock.
        self.refresh()

    def render(self) -> str:
        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0:
            return ""
        rows = field(width, height, getattr(self, "phase", 0.0), self.seed)
        return "\n".join(row(values, self.ramp) for values in rows)


@visual("idle", event="tick", glyphs="ascii")
class PlainIdle(Idle):
    ramp = ASCII


@visual("idle", event="tick", glyphs="blocks")
class BlockIdle(Idle):
    ramp = BLOCKS


@visual("idle", event="tick", glyphs="braille")
class BrailleIdle(Idle):
    ramp = BRAILLE
