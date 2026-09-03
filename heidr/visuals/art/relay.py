import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines

# Somebody else's aerial, a long way off. Shown while a public receiver is being
# listened through: the mast stands on a horizon and the waves it hears arrive
# as arcs spreading over the ground toward the near edge of the screen.
#
# The mast is on the right and small, and the arcs open toward the reader,
# because the whole point of the module is that the antenna is not here.
ASPECT = 2.0
MAST_SHARE = 0.78
HORIZON = 3
SPACING = 7.0
SPEED = 0.9
ARCS = 5


class Relay(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        ground = max(1, frame.height - HORIZON)
        foot = int(frame.width * MAST_SHARE)
        top = max(0, ground - max(3, frame.height // 2))

        for column in range(frame.width):
            grid[ground][column] = self.ramp[max(1, len(self.ramp) // 3)]

        # The mast, with its guys, and the light on top of it.
        line(grid, foot, ground, foot, top, self.ramp[-1])
        line(grid, foot, top + 1, foot - 6, ground - 1, self.ramp[max(1, len(self.ramp) // 3)])
        line(grid, foot, top + 1, foot + 6, ground - 1, self.ramp[max(1, len(self.ramp) // 3)])

        for number in range(ARCS):
            radius = (frame.tick * SPEED + number * SPACING) % (SPACING * ARCS)
            if radius < 1:
                continue
            # Fainter the further it has travelled, which is the one honest
            # thing anybody can say about a signal from far away.
            level = max(1, round((1 - radius / (SPACING * ARCS)) * (len(self.ramp) - 1)))
            self.arc(grid, frame, foot, top, radius, self.ramp[level])
        return lines(grid)

    def arc(self, grid, frame: Frame, foot: int, top: int, radius: float, mark: str) -> None:
        steps = max(8, int(radius * 4))
        for step in range(steps + 1):
            # A half circle opening away from the mast and toward the reader.
            angle = math.pi / 2 + step * math.pi / steps
            x = round(foot + radius * ASPECT * math.sin(angle))
            y = round(top + 1 - radius * math.cos(angle))
            if 0 <= y < frame.height and 0 <= x < frame.width and grid[y][x] == " ":
                grid[y][x] = mark


@animation("relay", glyphs="ascii", fps=12)
class PlainRelay(Relay):
    ramp = ASCII


@animation("relay", glyphs="blocks", fps=12)
class BlockRelay(Relay):
    ramp = BLOCKS


@animation("relay", glyphs="braille", fps=12)
class BrailleRelay(Relay):
    ramp = BRAILLE
