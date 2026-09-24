from functools import cache

from heidr.registry import animation
from heidr.visuals.art.runestone import INSCRIPTION
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import blank, lines, stamp

# The laser etch of TerminalTextEffects by Chris Builds
# (https://github.com/ChrisBuilds/terminaltexteffects, MIT), run as it is on the
# line of the Völuspá that `runestone` cuts by hand. Nothing is copied: the
# library is called, so this animation exists only where it is installed, which
# is the `effects` extra and the released binary.
#
# The library draws a whole film at once and keeps its own randomness, so the
# film is made once for the run and played back by the tick. That is what keeps
# a repainted tick the same picture. Making it takes most of a second, which is
# why it is only as large as the text and its sparks and is centred in whatever
# frame there is: a film the size of the terminal would be made again on every
# resize.
try:
    from terminaltexteffects.effects.effect_laseretch import LaserEtch
except ImportError:
    LaserEtch = None

WORDS = INSCRIPTION.rstrip("᛬").split("᛬")
# One word to a line, so the film is narrow enough to stand beside the panel
# rather than behind it, once at each edge of the screen.
TEXT = "\n".join(WORDS)
MARGIN = 3
# The finished text stays for this many frames before the laser starts again.
HOLD = 40


# The first showing waits for the film on the interface thread. If that pause
# is ever noticed, the film belongs in a worker.
@cache
def film() -> list[list[str]]:
    effect = LaserEtch(TEXT)
    effect.terminal_config.no_color = True
    effect.terminal_config.frame_rate = 0
    effect.terminal_config.canvas_width = max(map(len, TEXT.split("\n"))) + MARGIN * 2
    effect.terminal_config.canvas_height = TEXT.count("\n") + 1 + MARGIN
    effect.terminal_config.ignore_terminal_dimensions = True
    effect.terminal_config.anchor_text = "c"
    frames = [frame.split("\n") for frame in effect]
    return frames + [frames[-1]] * HOLD


class Etch(Painter):
    def paint(self, frame: Frame) -> list[str]:
        frames = film()
        grid = blank(frame.width, frame.height)
        width, height = len(frames[0][0]), len(frames[0])
        top = (frame.height - height) // 2
        # The second copy runs half a film behind the first, so the two edges
        # are never at the same moment.
        for left, lag in ((1, 0), (frame.width - width - 1, len(frames) // 2)):
            if left >= 0:
                stamp(grid, frames[(frame.tick + lag) % len(frames)], left, top)
        return lines(grid)


# A rune needs a font that has it, so there is no ascii version, exactly as
# with `runes`.
if LaserEtch is not None:
    animation("etch", glyphs="blocks", fps=12)(Etch)
