import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import blank, lines

# A word-frequency histogram collapsing until one column is left standing.
# Shown while the rarest module is at work, which throws away every ordinary
# word of a question and keeps the one nobody says.
#
# The shape is Zipf's law: the commonest word turns up about twice as often as
# the second, three times as often as the third, and so on down a curve that
# holds for every language anybody has counted. The rarest word is the flat tail
# at the right, which is the column that survives here.
#
# Plotted logarithmically, which is how that law is always drawn and the only
# way it fits a terminal: on a straight scale the twenty-sixth bar is a
# twenty-sixth of the height, and the whole tail is one row of dots.
BARS = 26
COLLAPSE = 16
BAR_WIDTH = 2
GAP = 1


def heights(count: int) -> list[float]:
    return [1 - math.log(place + 1) / math.log(count + 1) for place in range(count)]


def paint(frame: Frame) -> list[str]:
    grid = blank(frame.width, frame.height)
    floor = frame.height - 1
    count = min(BARS, max(1, (frame.width - GAP) // (BAR_WIDTH + GAP)))
    span = heights(count)
    # Everything falls except the last column, and it falls in order, so the
    # curve is eaten from the common end toward the rare one.
    gone = min(count - 1, frame.tick * count // max(1, COLLAPSE))

    for place, share in enumerate(span):
        if place < gone:
            continue
        left = GAP + place * (BAR_WIDTH + GAP)
        tall = max(1, round(share * (frame.height - 1)))
        survivor = place == count - 1
        mark = frame.ramp[-1] if survivor and gone == count - 1 else frame.ramp[len(frame.ramp) // 2]
        for row in range(tall):
            y = floor - row
            for column in range(BAR_WIDTH):
                if 0 <= y < frame.height and 0 <= left + column < frame.width:
                    grid[y][left + column] = mark
    return lines(grid)


for level in ("ascii", "blocks", "braille"):
    animation("zipf", glyphs=level, fps=10)(paint)
