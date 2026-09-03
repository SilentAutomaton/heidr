from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines, stamp

# A line folding about a vertical axis and coming back as its opposite. Shown
# while the reversal module is at work, which asks a model to turn a question
# into the question that means the other thing.
SAID = "should the aerial go on the roof"
MEANT = "should the aerial stay off the roof"
SWEEP = 0.55
PAUSE = 8


class Mirror(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        middle = frame.height // 2
        axis = frame.width // 2
        mark = "|" if frame.glyphs == "ascii" else "│"
        for row in range(frame.height):
            grid[row][axis] = mark

        # The question arrives at the axis from the left and its opposite leaves
        # on the other side, a letter at a time, then it starts again.
        longest = max(len(SAID), len(MEANT))
        shown = min(longest, int(frame.tick * SWEEP) % (longest + PAUSE))
        if shown:
            said = SAID[-shown:]
            stamp(grid, [said], max(0, axis - len(said)), middle - 1)
            meant = MEANT[:shown]
            stamp(grid, [meant], axis + 1, middle + 1)
        return lines(grid)


@animation("mirror", glyphs="ascii", fps=12)
class PlainMirror(Mirror):
    ramp = ASCII


@animation("mirror", glyphs="blocks", fps=12)
class BlockMirror(Mirror):
    ramp = BLOCKS


@animation("mirror", glyphs="braille", fps=12)
class BrailleMirror(Mirror):
    ramp = BRAILLE
