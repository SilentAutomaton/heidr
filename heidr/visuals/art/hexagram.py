from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, blank, centre, lines

# Six lines, built from the bottom up, the way a hexagram is cast. Shown while
# the stalks are being counted.
YANG = "  -----------  "
YIN = "  ----   ----  "
BLANK = "               "
LINES = 6
HOLD = 3


class Hexagram(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        drawn = min(LINES, frame.tick // HOLD)
        art = []
        for place in range(LINES):
            # The bottom line is cast first, so the drawing grows upward.
            from_bottom = LINES - 1 - place
            if from_bottom < drawn:
                art.append(YANG if (from_bottom + frame.tick // (HOLD * LINES)) % 2 else YIN)
            else:
                art.append(BLANK)
            art.append(BLANK)
        return lines(centre(blank(frame.width, frame.height), art[:-1]))


@animation("hexagram", glyphs="ascii", fps=4)
class PlainHexagram(Hexagram):
    ramp = ASCII


@animation("hexagram", glyphs="blocks", fps=4)
class BlockHexagram(Hexagram):
    ramp = BLOCKS
