from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, centre, lines

# Heiðr herself: hooded, staff in hand, waiting to be asked. Drawn for this
# project — the ASCII collections that exist aggregate other people's work with
# no clean provenance, and none of them had a völva in them.
#
# The drawing is fixed and single characters are overwritten at known positions
# each frame. Substituting whole words would let a longer replacement shift a
# line and bend her face, which is exactly what happened first time.
FIGURE = (
    "  |         .-~~~-.     ",
    "  |       ,'       ',   ",
    "  |      /  o   o   \\   ",
    "  |     |     v      |  ",
    "  |     |    ---     |  ",
    "  |      \\          /   ",
    "  O       '.,___,.'     ",
    "  |       /   |   \\     ",
)

# row, column
STAFF_TIP = (0, 2)
EYES = ((2, 12), (2, 16))
MOUTH = (4, 13)  # the middle of three dashes
HEM = ((7, 10), (7, 18))

BLINK_EVERY = 17
MOUTHS = "----~~--"
HEM_LEFT = "/|\\|"
HEM_RIGHT = "\\|/|"


def figure(tick: int, ramp: str) -> list[str]:
    rows = [list(line) for line in FIGURE]

    # The staff answers first: its head brightens before she speaks.
    rows[STAFF_TIP[0]][STAFF_TIP[1]] = ramp[-1] if tick % 4 < 2 else ramp[max(1, len(ramp) // 2)]

    blinking = tick % BLINK_EVERY == BLINK_EVERY - 1
    for row_number, column in EYES:
        rows[row_number][column] = "-" if blinking else "o"

    rows[MOUTH[0]][MOUTH[1]] = MOUTHS[tick % len(MOUTHS)]

    left, right = HEM
    rows[left[0]][left[1]] = HEM_LEFT[tick // 2 % len(HEM_LEFT)]
    rows[right[0]][right[1]] = HEM_RIGHT[tick // 2 % len(HEM_RIGHT)]

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
