from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines, stamp

# Letters dropping onto an abacus, each pushing as many beads across as it is
# worth, and a total growing underneath. Shown while the gematria module is at
# work, which is exactly this: letters become numbers, and their sum is the key.
LETTERS = "HEIDR"
WIRES = 5
FALL = 0.6
HOLD = 9
BEADS = 9


def worth(character: str) -> int:
    """A letter's place in the alphabet, folded to one digit as gematria does."""
    return (ord(character.upper()) - ord("A")) % BEADS + 1


class Abacus(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        wire = self.ramp[max(1, len(self.ramp) // 3)]
        bead = self.ramp[-1]
        left = max(1, frame.width // 2 - BEADS - 4)
        top = max(1, frame.height // 2 - WIRES // 2)
        total = 0

        for number in range(WIRES):
            row = top + number
            if row >= frame.height:
                break
            for column in range(BEADS + 2):
                if left + column < frame.width:
                    grid[row][left + column] = wire

            character = LETTERS[number % len(LETTERS)]
            landed = frame.tick - number * HOLD - int(row / FALL)
            if landed >= 0:
                total += worth(character)
                for count in range(worth(character)):
                    if left + 1 + count < frame.width:
                        grid[row][left + 1 + count] = bead
            else:
                self.falling(grid, frame, character, left - 2, row, frame.tick - number * HOLD)

        if total:
            stamp(grid, [str(total)], left, min(frame.height - 1, top + WIRES + 1))
        return lines(grid)

    def falling(self, grid, frame: Frame, character: str, x: int, floor: int, age: int) -> None:
        if age < 0:
            return
        y = int(age * FALL)
        if 0 <= y <= floor and 0 <= x < frame.width:
            grid[y][x] = character


@animation("abacus", glyphs="ascii", fps=10)
class PlainAbacus(Abacus):
    ramp = ASCII


@animation("abacus", glyphs="blocks", fps=10)
class BlockAbacus(Abacus):
    ramp = BLOCKS


@animation("abacus", glyphs="braille", fps=10)
class BrailleAbacus(Abacus):
    ramp = BRAILLE
