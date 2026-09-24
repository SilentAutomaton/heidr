import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import BLOCKS, BRAILLE, blank, lines

# Two standing stones, and a line of the Völuspá being cut into them one rune
# at a time. The line is stanza 22, "Heiði hana hétu": Heiðr they called her,
# wherever she came to a house. It is the only place the name of this program
# is written down, and the Younger Futhark is what a runestone of her century
# would have been cut in. The spelling follows the stones: no letter for e, so
# the diphthong is written a-i, and a word ends in a divider, ᛬.
#
# The cut is the laser etch of TerminalTextEffects by Chris Builds
# (https://github.com/ChrisBuilds/terminaltexteffects, MIT) slowed to a knife: a
# spark where the blade is and the finished letters behind it. Only the idea
# was taken; the library is used as it is by `etch`.
#
# The inscription runs in a band inside the edge of the stone, up one side,
# over the top and down the other, which is how most Swedish stones carry it.
# The stones stand at the two edges of the screen, as the pair at Jelling stand
# either side of the church, because the panel covers the middle: a stone
# drawn there would be cut where nobody can see it.
INSCRIPTION = "ᚼᛅᛁᚦᛁ᛬ᚼᛅᚾᛅ᛬ᚼᛁᛏᚢ᛬ᚢᛅᛚᚢ᛬ᚢᛁᛚᛋᛒᛅ᛬"
TALLEST = 22
# A terminal cell is about twice as tall as it is wide, so a stone that looks
# a little taller than wide is this many columns for each row.
ASPECT = 1.3
# The share of the width each stone may take, which keeps it clear of a panel
# of the usual width.
SIDE = 5
INSET = 2
CUT = 3
HOLD = 48
# Half the inscription is cut on each stone, so the length of a whole pass is
# known before any stone is drawn.
CYCLE = len(INSCRIPTION) // 2 * 2 * CUT + HOLD


def halves(height: int, half: int) -> list[int]:
    """The half width of the stone on each row: a rounded head on a straight body."""
    head = max(1, height // 3)
    widths = []
    for row in range(height):
        if row < head:
            rise = (head - row - 0.5) / head
            widths.append(max(1, round(half * math.sqrt(1 - rise * rise))))
        else:
            widths.append(half)
    return widths


def band(widths: list[int], centre: int) -> list[tuple[int, int]]:
    """The cells the inscription runs along, in reading order."""
    top = next((row for row, half in enumerate(widths) if row > 1 and half > INSET + 1), len(widths))
    bottom = len(widths) - 2
    up = [(row, centre - widths[row] + INSET) for row in range(bottom, top, -1)]
    across = [(top, column) for column in range(centre - widths[top] + INSET, centre + widths[top] - INSET + 1)]
    down = [(row, centre + widths[row] - INSET) for row in range(top + 1, bottom + 1)]
    return up + across + down


class Runestone(Painter):
    """The stones are still; only the knife moves, then the whole text rests.

    Everything comes from the tick, so the same tick paints the same stones.
    """

    ramp = BLOCKS

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        height = min(TALLEST, frame.height - 1)
        half = min(frame.width // SIDE // 2, round(height * ASPECT / 2))
        if height < 6 or half < INSET + 2:
            return lines(grid)

        top = frame.height - 1 - height
        ground = frame.height - 1
        for column in range(frame.width):
            grid[ground][column] = self.ramp[1]

        widths = halves(height, half)
        places = []
        for centre in (half + 1, frame.width - half - 2):
            self.stone(grid, widths, centre, top)
            path = band(widths, centre)
            share = len(INSCRIPTION) // 2
            # The text is spread along the band rather than packed at its
            # start, so a tall stone is not cut on one side only.
            places += [(top + row, column) for row, column in (path[number * len(path) // share] for number in range(share))]

        age = frame.tick % CYCLE
        cut = min(len(places), age // CUT)
        for number in range(cut):
            row, column = places[number]
            grid[row][column] = INSCRIPTION[number]
        if cut < len(places):
            row, column = places[cut]
            grid[row][column] = self.ramp[-1] if age % 2 else self.ramp[-3]
        return lines(grid)

    def stone(self, grid, widths: list[int], centre: int, top: int) -> None:
        # Each edge is a stave or a slant, and where the head widens by more
        # than one column the step is closed with a flat cut, as in `_/`.
        for column in range(centre - widths[0], centre + widths[0] + 1):
            grid[top][column] = "_"
        for row in range(1, len(widths)):
            width, above = widths[row], widths[row - 1]
            grown = width > above
            grid[top + row][centre - width] = "/" if grown else "|"
            grid[top + row][centre + width] = "\\" if grown else "|"
            for step in range(above + 1, width):
                grid[top + row - 1][centre - step] = "_"
                grid[top + row - 1][centre + step] = "_"


@animation("runestone", glyphs="blocks", fps=8)
class BlockRunestone(Runestone):
    ramp = BLOCKS


@animation("runestone", glyphs="braille", fps=8)
class BrailleRunestone(Runestone):
    ramp = BRAILLE
