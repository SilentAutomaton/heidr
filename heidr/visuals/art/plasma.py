import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import row

# Four sine waves radiating from four points, summed. The classic plasma of
# Lode Vandevenne's tutorial at http://lodev.org/cgtutor/plasma.html, by way of
# asciimatics by Peter Brittain (Apache-2.0), where the constants below come
# from. https://github.com/peterbrittain/asciimatics
#
# It replaces a field of three straight sine waves, which read as corduroy.
# Waves radiating from points read as something alive.
SOURCES = ((1 / 4, 1 / 3, 15), (1 / 8, 1 / 5, 11), (1 / 2, 1 / 5, 13), (3 / 4, 4 / 5, 13))
QUIET = 1.6


def wave(x: float, y: float, width: int, height: int, across: float, down: float, scale: float) -> float:
    distance = math.sqrt((x - width * across) ** 2 + 4 * ((y - height * down) ** 2))
    return math.sin(distance * math.pi / scale)


def field(width: int, height: int, phase: float) -> list[list[float]]:
    rows = []
    for y in range(height):
        values = []
        for x in range(width):
            total = (
                wave(x + phase, y, width, height, *SOURCES[0])
                + wave(x, y, width, height, *SOURCES[1])
                + wave(x, y + phase, width, height, *SOURCES[2])
                + wave(x, y, width, height, *SOURCES[3])
            )
            # Biased downward: this sits behind text that has to stay readable.
            values.append((abs(total) / 4.0) ** QUIET)
        rows.append(values)
    return rows


def paint(frame: Frame) -> list[str]:
    return [row(values, frame.ramp) for values in field(frame.width, frame.height, frame.tick / 3)]


for level in ("ascii", "blocks", "braille"):
    animation("plasma", glyphs=level, fps=8)(paint)
