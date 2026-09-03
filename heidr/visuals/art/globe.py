import math

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, lines

# A wire globe turning, with a mark lighting where each station is. Shown while
# the internet radio source is listening, which is a thing that happens all over
# the world at once and looks nothing like a spectrum sweep.
#
# Meridians and parallels are drawn as points rather than as strokes: a sphere
# in a terminal is thirty rows tall at best, and a stroked wireframe at that
# size turns into a solid disc.
ASPECT = 2.0
MERIDIANS = 12
PARALLELS = 7
POINTS = 46
SPIN = 0.055
# Roughly where a few of the loudest cities are, in degrees. Not a map, and not
# meant to be read as one: the point is that the marks are somewhere real.
STATIONS = ((52.0, 13.0), (40.0, -74.0), (35.0, 139.0), (-23.0, -46.0), (55.0, 37.0), (-34.0, 151.0))


def spherical(latitude: float, longitude: float, turn: float) -> tuple[float, float, float]:
    """A point on the globe as it is seen now, with depth kept for hiding."""
    phi = math.radians(latitude)
    theta = math.radians(longitude) + turn
    return math.cos(phi) * math.sin(theta), math.sin(phi), math.cos(phi) * math.cos(theta)


class Globe(Painter):
    ramp = ASCII

    def plot(self, grid, frame: Frame, x: float, y: float, depth: float, mark: str) -> None:
        # The far side of the globe is behind the near side, so it is not drawn.
        if depth < 0:
            return
        across, down = frame.width / 2, frame.height / 2
        radius = max(2.0, min(down - 0.5, frame.width / ASPECT / 2 - 0.5))
        column = round(across + x * radius * ASPECT)
        line = round(down - y * radius)
        if 0 <= line < frame.height and 0 <= column < frame.width:
            grid[line][column] = mark

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        turn = frame.tick * SPIN
        faint = self.ramp[max(1, len(self.ramp) // 3)]

        for number in range(MERIDIANS):
            longitude = number * 360 / MERIDIANS
            for step in range(POINTS):
                latitude = -90 + step * 180 / (POINTS - 1)
                self.plot(grid, frame, *spherical(latitude, longitude, turn), faint)

        for number in range(PARALLELS):
            latitude = -75 + number * 150 / (PARALLELS - 1)
            for step in range(POINTS):
                longitude = step * 360 / POINTS
                self.plot(grid, frame, *spherical(latitude, longitude, turn), faint)

        for latitude, longitude in STATIONS:
            self.plot(grid, frame, *spherical(latitude, longitude, turn), self.ramp[-1])
        return lines(grid)


@animation("globe", glyphs="ascii", fps=12)
class PlainGlobe(Globe):
    ramp = ASCII


@animation("globe", glyphs="blocks", fps=12)
class BlockGlobe(Globe):
    ramp = BLOCKS


@animation("globe", glyphs="braille", fps=12)
class BrailleGlobe(Globe):
    ramp = BRAILLE
