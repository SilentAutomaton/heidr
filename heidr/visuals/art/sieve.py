from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines, stamp

# Words shaken until the vowels fall out of them. Shown while the skeleton
# module is at work, which drops the vowels of a question and keeps the
# consonant root — so the picture is the method rather than a decoration of it.
WORDS = ("question", "answer", "listen", "signal", "evening", "roof", "aerial", "silence")
VOWELS = "aeiouy"
FALL = 0.7
HOLD = 6


def sifted(word: str) -> str:
    return "".join(character for character in word if character not in VOWELS)


class Sieve(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        bar = max(1, frame.height // 3)
        for column in range(frame.width):
            grid[bar][column] = self.ramp[max(1, len(self.ramp) // 3)]

        for number, word in enumerate(WORDS):
            # Each word is shaken a little after the one before it, so the
            # screen is never all falling or all still.
            age = frame.tick - number * HOLD
            if age < 0:
                continue
            left = 2 + (number * 11) % max(1, frame.width - len(word) - 4)
            stamp(grid, [sifted(word)], left, max(0, bar - 2 - number % 3))
            self.drop(grid, frame, word, left, bar, age)
        return lines(grid)

    def drop(self, grid, frame: Frame, word: str, left: int, bar: int, age: int) -> None:
        for offset, character in enumerate(word):
            if character not in VOWELS:
                continue
            # A vowel keeps the column it was written in and falls through the
            # bar, which is what makes the sieve read as a sieve.
            y = bar + 1 + int(age * FALL)
            if 0 <= y < frame.height and 0 <= left + offset < frame.width:
                grid[y][left + offset] = character


@animation("sieve", glyphs="ascii", fps=10)
class PlainSieve(Sieve):
    ramp = ASCII


@animation("sieve", glyphs="blocks", fps=10)
class BlockSieve(Sieve):
    ramp = BLOCKS


@animation("sieve", glyphs="braille", fps=10)
class BrailleSieve(Sieve):
    ramp = BRAILLE
