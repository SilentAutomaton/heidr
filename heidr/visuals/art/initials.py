from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines, stamp

# A stack of words, and their first letters lifting out of it and lining up.
# Shown while the acrostic module is at work, which reads the initials of a
# question as a word of its own.
#
# Their initials spell RADIO, which is what the program listens to and the
# shortest honest demonstration of what an acrostic is.
WORDS = ("reach", "answer", "does", "it", "open")
LIFT = 5
RISE = 0.34


class Initials(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        left = max(1, frame.width // 2 - 12)
        line = max(2, frame.height - len(WORDS) - 2)

        for number, word in enumerate(WORDS):
            row = line + number
            # The rest of the word stays where it was written; only the first
            # letter travels, so the reader can see where each one came from.
            stamp(grid, [" " + word[1:]], left, row)
            travelled = max(0, int((frame.tick - number * LIFT) * RISE))
            if row - travelled <= 0:
                self.place(grid, frame, word[0], left + number, 0)
            else:
                self.place(grid, frame, word[0], left, row - travelled)
        return lines(grid)

    def place(self, grid, frame: Frame, character: str, x: int, y: int) -> None:
        if 0 <= y < frame.height and 0 <= x < frame.width:
            grid[y][x] = character


@animation("initials", glyphs="ascii", fps=10)
class PlainInitials(Initials):
    ramp = ASCII


@animation("initials", glyphs="blocks", fps=10)
class BlockInitials(Initials):
    ramp = BLOCKS


@animation("initials", glyphs="braille", fps=10)
class BrailleInitials(Initials):
    ramp = BRAILLE
