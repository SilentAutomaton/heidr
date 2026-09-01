from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, centre, lines

# Heiðr herself: hooded, staff in hand, waiting to be asked. Drawn for this
# project. The ASCII galleries that do this best — Joan Stark's above all — are
# marked all rights reserved with a demand to keep the artist's initials on
# every copy, which no GPL repository can honour. So the technique is borrowed
# and the drawing is not: density for tone, shadow inside the cowl, a face made
# of three marks, a silhouette that widens toward the hem.
FIGURE = (
    "  (@)          _.-~~~~~-._        ",
    "   |         .'           `.      ",
    "   |        /  .:'~~~~~':.  \\     ",
    "   |       |  ::         ::  |    ",
    "   |       |  ::   o o   ::  |    ",
    "   |       |  ::.   ~   .::  |    ",
    "   |       \\  ':.._____.:'  /     ",
    "   |        `._           _.'     ",
    "   |          `-.._____.-'        ",
    "   |           /         \\        ",
    "   |           / |     | \\        ",
    "   |          /  |     |  \\       ",
    "   |          /  |     |  \\       ",
    "   |         /  |       |  \\      ",
    "   |         /  |       |  \\      ",
    "   |        /   |       |   \\     ",
    "   |        /   |       |   \\     ",
    "   |       /    |       |    \\    ",
    "   |       /    |       |    \\    ",
    "   |      /    |         |    \\   ",
    "   |      /    |         |    \\   ",
    "   |     /     |         |     \\  ",
    "   |     /_____________________\\  ",
)

STAFF_COLUMN = 3
EYE_ROW, MOUTH_ROW = 4, 5
# Only the lowest row of the drape moves: cloth swings at the hem, not halfway
# up, and a fold that flickers along its whole length reads as damage.
HEM_ROWS = (21,)
BLINK_EVERY = 17
MOUTHS = "~~--~~..~~--"
SWAY = "|/|\\"


def _columns(row: int, character: str) -> tuple[int, ...]:
    """Where a mark sits in the drawing, found rather than written down.

    The figure changed once and the hand written coordinates did not, which is
    how her face came to be bent. Now the drawing is the only source.
    """
    return tuple(number for number, found in enumerate(FIGURE[row]) if found == character)


EYES = _columns(EYE_ROW, "o")
MOUTH = _columns(MOUTH_ROW, "~")
STAFF = (0, FIGURE[0].index("@"))
FOLDS = tuple(
    (row, column)
    for row in HEM_ROWS
    for column in _columns(row, "|")
    if column != STAFF_COLUMN
)


def figure(tick: int, ramp: str) -> list[str]:
    rows = [list(line) for line in FIGURE]

    # The staff answers first: its head brightens before she speaks.
    rows[STAFF[0]][STAFF[1]] = "@" if tick % 4 < 2 else ramp[len(ramp) // 2]

    blinking = tick % BLINK_EVERY == BLINK_EVERY - 1
    for column in EYES:
        rows[EYE_ROW][column] = "-" if blinking else "o"

    for column in MOUTH:
        rows[MOUTH_ROW][column] = MOUTHS[tick % len(MOUTHS)]

    # The hem moves last and least, the way heavy cloth does.
    for number, (row, column) in enumerate(FOLDS):
        rows[row][column] = SWAY[(tick // 3 + number) % len(SWAY)]

    return ["".join(row) for row in rows]


class Seeress(Painter):
    """She breathes, the staff glimmers, and now and then she blinks.

    Slow on purpose. A figure that fidgets reads as impatient, and this one has
    been waiting a thousand years.
    """

    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        return lines(centre(blank(frame.width, frame.height), figure(frame.tick, self.ramp)))


@animation("seeress", glyphs="ascii", fps=3)
class PlainSeeress(Seeress):
    ramp = ASCII


@animation("seeress", glyphs="blocks", fps=3)
class BlockSeeress(Seeress):
    ramp = BLOCKS


@animation("seeress", glyphs="braille", fps=3)
class BrailleSeeress(Seeress):
    ramp = BRAILLE
