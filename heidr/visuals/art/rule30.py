from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE

# Rule 30, Stephen Wolfram, 1983. One line of cells, one rule, and the next line
# is read off it: a cell is alive when its left neighbour differs from the pair
# on its right. Started from a single live cell it grows nested triangles down
# one side and never settles down the other, and that asymmetry is why it was
# used as a random number generator for years.
#
# Which makes it the right rule for this program rather than a decoration. The
# rules are not ours to adjust, the same way Conway's are not.
#
# Langton's ant was tried first and does not work here: on a board the size of a
# terminal it fills up with even noise long before it starts building its road.
BIRTH = {(1, 0, 0), (0, 1, 1), (0, 1, 0), (0, 0, 1)}
FADE = 3


def step(cells: tuple[int, ...]) -> tuple[int, ...]:
    """One generation. The row wraps, so the pattern has no edge to die at."""
    width = len(cells)
    return tuple(
        1 if (cells[(index - 1) % width], cells[index], cells[(index + 1) % width]) in BIRTH else 0
        for index in range(width)
    )


class Rule30(Painter):
    """One new line per frame, the older ones scrolling up and fading."""

    ramp = ASCII

    def __init__(self):
        self.rows: list[tuple[int, ...]] = []
        self.width = 0
        self.last_tick = -1

    def sow(self, width: int) -> None:
        self.width = width
        # One live cell, which is the only starting line worth having: anything
        # else hides the triangles under its own pattern.
        self.rows = [tuple(1 if index == width // 2 else 0 for index in range(width))]

    def paint(self, frame: Frame) -> list[str]:
        if self.width != frame.width:
            self.sow(frame.width)
        elif frame.tick != self.last_tick:
            self.rows.append(step(self.rows[-1]))
            del self.rows[: -frame.height]
        self.last_tick = frame.tick

        shown = self.rows[-frame.height :]
        blank = " " * frame.width
        lines = [blank] * (frame.height - len(shown))
        for age, cells in enumerate(reversed(shown)):
            # The newest line is brightest; older ones sink into the ramp as
            # they climb, so the eye follows the growing edge.
            level = max(1, len(self.ramp) - 1 - age // FADE)
            mark = self.ramp[level]
            lines.append("".join(mark if cell else " " for cell in cells))
        return lines[-frame.height :]


@animation("rule30", glyphs="ascii", fps=10)
class PlainRule30(Rule30):
    ramp = ASCII


@animation("rule30", glyphs="blocks", fps=10)
class BlockRule30(Rule30):
    ramp = BLOCKS


@animation("rule30", glyphs="braille", fps=10)
class BrailleRule30(Rule30):
    ramp = BRAILLE
