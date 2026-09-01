from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines, resample

# The spectrum drawn as a trace across the middle rather than as a falling
# waterfall: the same numbers, read the way an oscilloscope reads them.


class Scope(Painter):
    ramp = ASCII

    def __init__(self):
        self.bars: list[float] = []

    def feed(self, payload) -> None:
        if payload:
            self.bars = list(payload)

    def paint(self, frame: Frame) -> list[str]:
        if not self.bars:
            return []
        grid = blank(frame.width, frame.height)
        middle = (frame.height - 1) / 2
        points = resample(self.bars, frame.width)

        previous = None
        for column, value in enumerate(points):
            # Centred: the trace swings either side of the line, as it would on
            # a real screen.
            y = round(middle - (value - 0.5) * (frame.height - 1))
            if previous is not None:
                line(grid, column - 1, previous, column, y, self.ramp[-1])
            previous = y
        return lines(grid)


@animation("scope", glyphs="ascii", fps=12, event="spectrum")
class PlainScope(Scope):
    ramp = ASCII


@animation("scope", glyphs="blocks", fps=12, event="spectrum")
class BlockScope(Scope):
    ramp = BLOCKS


@animation("scope", glyphs="braille", fps=12, event="spectrum")
class BrailleScope(Scope):
    ramp = BRAILLE
