from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import BLOCKS, BRAILLE

# The Elder Futhark, drifting upward and fading. The program is named for Heiðr,
# the völva of the Völuspá, and until now nothing on the screen said so. The
# alphabet is about eighteen hundred years old and belongs to nobody.
#
# A rune is one character wide in a monospace font and three or four hundred
# years older than the idea of one, so nothing is drawn at ascii level: a
# console without the glyphs would show a screen of empty squares. There the
# animation is simply not chosen, exactly as the braille waterfall is not.
FUTHARK = "ᚠᚢᚦᚨᚱᚲᚷᚹᚺᚾᛁᛃᛇᛈᛉᛊᛏᛒᛖᛗᛚᛜᛞᛟ"
COLUMNS_IN_USE = 0.28
RISE = 0.55
PERIOD = 40


class Runes(Painter):
    """Rising letters, each fading as it climbs, on a fixed set of columns.

    Nothing is random here. A rune's column, its speed and which letter it is
    all come from arithmetic on its number, so the same tick paints the same
    screen however often it is repainted.
    """

    ramp = BLOCKS

    def rows(self, frame: Frame) -> list[list[str]]:
        grid = [[" "] * frame.width for _ in range(frame.height)]
        count = max(1, int(frame.width * COLUMNS_IN_USE))
        for number in range(count):
            column = (number * 7 + 3) % frame.width
            offset = (number * 13) % PERIOD
            age = (frame.tick + offset) % PERIOD
            y = frame.height - 1 - int(age * RISE)
            if 0 <= y < frame.height:
                grid[y][column] = FUTHARK[(number * 5 + age // 8) % len(FUTHARK)]
            # A short wake below it, so a rune reads as rising rather than as
            # blinking somewhere new.
            for trail in range(1, 4):
                below = y + trail
                if 0 <= below < frame.height:
                    level = len(self.ramp) - 1 - trail
                    grid[below][column] = self.ramp[max(1, level)]
        return grid

    def paint(self, frame: Frame) -> list[str]:
        return ["".join(line) for line in self.rows(frame)]


@animation("runes", glyphs="blocks", fps=8)
class BlockRunes(Runes):
    ramp = BLOCKS


@animation("runes", glyphs="braille", fps=8)
class BrailleRunes(Runes):
    ramp = BRAILLE
