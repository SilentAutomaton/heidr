from collections import deque

from heidr.registry import visual
from heidr.visuals.base import ASCII, BLOCKS, BRAILLE, Visualisation, resample, row

# An ASCII spectrum scrolling in the terminal, in the register set by
# retrogram-rtlsdr by r4d10n. https://github.com/r4d10n/retrogram-rtlsdr
DEPTH = 64


class Waterfall(Visualisation):
    ramp = ASCII

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rows: deque[list[float]] = deque(maxlen=DEPTH)

    def feed(self, bars: list[float]) -> None:
        self.rows.append(list(bars))
        self.refresh()

    def render(self) -> str:
        width, height = self.size.width, self.size.height
        if width <= 0 or height <= 0 or not self.rows:
            return ""
        newest = list(self.rows)[-height:]
        return "\n".join(row(resample(bars, width), self.ramp) for bars in reversed(newest))


@visual("waterfall", event="spectrum", glyphs="ascii")
class PlainWaterfall(Waterfall):
    ramp = ASCII


@visual("waterfall", event="spectrum", glyphs="blocks")
class BlockWaterfall(Waterfall):
    ramp = BLOCKS


@visual("waterfall", event="spectrum", glyphs="braille")
class BrailleWaterfall(Waterfall):
    ramp = BRAILLE
