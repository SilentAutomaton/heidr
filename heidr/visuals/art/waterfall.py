from collections import deque

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, resample, row

# An ASCII spectrum scrolling in the terminal, in the register set by
# retrogram-rtlsdr by r4d10n. https://github.com/r4d10n/retrogram-rtlsdr
DEPTH = 64


class Waterfall(Painter):
    ramp = ASCII

    def __init__(self):
        self.rows: deque[list[float]] = deque(maxlen=DEPTH)

    def feed(self, payload) -> None:
        if payload:
            self.rows.append(list(payload))

    def paint(self, frame: Frame) -> list[str]:
        if not self.rows:
            return []
        newest = list(self.rows)[-frame.height :]
        return [row(resample(bars, frame.width), self.ramp) for bars in reversed(newest)]


@animation("waterfall", glyphs="ascii", event="spectrum")
class PlainWaterfall(Waterfall):
    ramp = ASCII


@animation("waterfall", glyphs="blocks", event="spectrum")
class BlockWaterfall(Waterfall):
    ramp = BLOCKS


@animation("waterfall", glyphs="braille", event="spectrum")
class BrailleWaterfall(Waterfall):
    ramp = BRAILLE
