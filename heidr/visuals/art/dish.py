import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, line, lines

# A dish tipped at the sky, and the noise floor breathing under it. Shown while
# the hydrogen line or a satellite pass is being listened for.
ASPECT = 2.0
NOISE_ROWS = 2


def hashed(x: int, y: int, tick: int) -> float:
    """Noise that belongs to a frame rather than to the moment of drawing.

    A live random number generator here would make the floor flicker at the
    terminal's repaint rate instead of the animation's, which is both wrong and
    unpleasant to look at.
    """
    mixed = (x * 73856093) ^ (y * 19349663) ^ (tick * 83492791)
    return (mixed % 1000) / 1000


class Dish(Painter):
    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        sky = max(1, frame.height - NOISE_ROWS)
        across = frame.width // 2
        radius = max(2, min(sky - 1, frame.width // 4))
        # The dish nods slowly, the way a tracking mount does.
        tilt = math.sin(frame.tick * 0.12) * 0.5

        # A parabola is what a dish is, so draw one and tip it.
        for step in range(-radius, radius + 1):
            depth = step * step / (2 * radius)
            x = round(across + (step * math.cos(tilt) - depth * math.sin(tilt)) * ASPECT)
            y = round(1 + step * math.sin(tilt) + depth * math.cos(tilt))
            if 0 <= y < sky and 0 <= x < frame.width:
                grid[y][x] = self.ramp[-1]

        # The mast, from under the bowl down to the ground.
        line(grid, across, min(sky - 1, 3), across, sky - 1, self.ramp[len(self.ramp) // 2])

        for row_number in range(frame.height - NOISE_ROWS, frame.height):
            for x in range(frame.width):
                level = abs(math.sin(x * 0.4 + frame.tick * 0.3)) * hashed(x, row_number, frame.tick)
                grid[row_number][x] = self.ramp[max(0, round(level * 3))]
        return lines(grid)


@animation("dish", glyphs="ascii", fps=8)
class PlainDish(Dish):
    ramp = ASCII


@animation("dish", glyphs="blocks", fps=8)
class BlockDish(Dish):
    ramp = BLOCKS


@animation("dish", glyphs="braille", fps=8)
class BrailleDish(Dish):
    ramp = BRAILLE
