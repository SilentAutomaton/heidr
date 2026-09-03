from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE

# A glass screen with the picture not quite locked: alternate lines are darker,
# a bright bar rolls slowly down, and the rest is snow. Shown while a live
# stream is being listened to, which is the one source in the program where
# somebody is talking into a camera.
#
# The snow is hashed from the position and the frame rather than drawn from a
# generator, so a repaint of one tick gives the same screen. A live generator
# here would make the picture flicker at the terminal's repaint rate instead of
# the animation's, which is both wrong and unpleasant to look at.
ROLL = 0.35
BAR = 3
SNOW = 0.24


def hashed(x: int, y: int, tick: int) -> float:
    mixed = (x * 73856093) ^ (y * 19349663) ^ (tick * 83492791)
    return (mixed % 1000) / 1000


class Scanlines(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        top = len(self.ramp) - 1
        bar = int(frame.tick * ROLL) % max(1, frame.height + BAR * 2) - BAR
        rows = []
        for y in range(frame.height):
            # Every other line is held back, which is what a scan line is.
            base = top if y % 2 == 0 else max(1, top // 2)
            inside = bar <= y < bar + BAR
            row = []
            for x in range(frame.width):
                noise = hashed(x, y, frame.tick)
                if inside:
                    row.append(self.ramp[top] if noise < 0.8 else self.ramp[base])
                elif noise < SNOW:
                    row.append(self.ramp[max(1, round(base * noise / SNOW))])
                else:
                    row.append(" ")
            rows.append("".join(row))
        return rows


@animation("scanlines", glyphs="ascii", fps=12)
class PlainScanlines(Scanlines):
    ramp = ASCII


@animation("scanlines", glyphs="blocks", fps=12)
class BlockScanlines(Scanlines):
    ramp = BLOCKS


@animation("scanlines", glyphs="braille", fps=12)
class BrailleScanlines(Scanlines):
    ramp = BRAILLE
