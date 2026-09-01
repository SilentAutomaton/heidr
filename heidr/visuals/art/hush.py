import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, blank, centre, lines

# Shown when the oracle keeps its mouth shut. This is the one place the program
# is allowed a joke: there is no answer anyway, so there is nothing to lose.
#
# The kaomoji are folklore with no author to credit. The drawn figures were made
# for this project.
QUIET = (
    "     .-\"\"\"-.     ",
    "    /  _ _  \\    ",
    "   |  (o)(o) |   ",
    "   |    <    |   ",
    "   |   ---   |   ",
    "    \\   |   /    ",
    "     '--|--'     ",
    "        |        ",
)

SHRUG_RICH = ("  ¯\\_(ツ)_/¯  ",)
SHRUG_PLAIN = ("   _\\_(o o)_/_   ",)
DISAPPROVAL_RICH = ("   ಠ_ಠ   ",)
DISAPPROVAL_PLAIN = ("   -_-   ",)

HANDS = ("   \\   |   /    ", "    \\  |  /     ", "   \\   |   /    ", "     \\ | /      ")


def figures(glyphs: str) -> list[tuple[str, ...]]:
    """What the silence can look like. Kaomoji only where they will render."""
    rich = glyphs in ("blocks", "braille")
    return [
        QUIET,
        SHRUG_RICH if rich else SHRUG_PLAIN,
        DISAPPROVAL_RICH if rich else DISAPPROVAL_PLAIN,
    ]


class Hush(Painter):
    ramp = ASCII
    glyphs = "ascii"

    def __init__(self):
        self.choice = random.Random().randrange(3)

    def paint(self, frame: Frame) -> list[str]:
        art = list(figures(frame.glyphs)[self.choice % len(figures(frame.glyphs))])
        if art is not QUIET and len(art) == 1:
            # A one-line kaomoji has nothing to animate, and should not pretend.
            return lines(centre(blank(frame.width, frame.height), art))
        art[5] = HANDS[frame.tick // 3 % len(HANDS)]
        return lines(centre(blank(frame.width, frame.height), art))


@animation("hush", glyphs="ascii", fps=3)
class PlainHush(Hush):
    ramp = ASCII


@animation("hush", glyphs="blocks", fps=3)
class BlockHush(Hush):
    ramp = BLOCKS
