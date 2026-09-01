"""The brushes every animation shares.

From flattest to richest. An animation declares the poorest terminal it can live
on, and the registry hands back the best one this terminal can draw.
"""

ASCII = " .:-=+*#%@"
BLOCKS = " ▁▂▃▄▅▆▇█"
BRAILLE = " ⣀⣄⣤⣦⣶⣷⣿"
LEVELS = ("ascii", "box", "blocks", "braille")


def resample(bars: list[float], width: int) -> list[float]:
    """Fit any number of bars into the columns actually on screen."""
    if width <= 0 or not bars:
        return []
    if len(bars) == width:
        return list(bars)

    out = []
    for column in range(width):
        start = column * len(bars) // width
        end = max(start + 1, (column + 1) * len(bars) // width)
        chunk = bars[start:end]
        out.append(sum(chunk) / len(chunk))
    return out


def row(bars: list[float], ramp: str) -> str:
    top = len(ramp) - 1
    return "".join(ramp[min(top, max(0, round(value * top)))] for value in bars)


def blank(width: int, height: int) -> list[list[str]]:
    return [[" "] * width for _ in range(height)]


def stamp(grid: list[list[str]], art: list[str], left: int, top: int) -> list[list[str]]:
    """Draw a block of text into a grid, clipped at the edges.

    Spaces in the art are transparent, so a figure can stand in front of a
    moving field without cutting a rectangle out of it.
    """
    for line_number, line in enumerate(art):
        y = top + line_number
        if not 0 <= y < len(grid):
            continue
        for column, character in enumerate(line):
            x = left + column
            if 0 <= x < len(grid[y]) and character != " ":
                grid[y][x] = character
    return grid


def centre(grid: list[list[str]], art: list[str]) -> list[list[str]]:
    height = len(grid)
    width = len(grid[0]) if grid else 0
    art_width = max((len(line) for line in art), default=0)
    return stamp(grid, art, (width - art_width) // 2, (height - len(art)) // 2)


def lines(grid: list[list[str]]) -> list[str]:
    return ["".join(line) for line in grid]


def line(grid: list[list[str]], x0: int, y0: int, x1: int, y1: int, mark: str) -> list[list[str]]:
    """Bresenham, because several animations plot curves point by point."""
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    step_x = 1 if x0 < x1 else -1
    step_y = 1 if y0 < y1 else -1
    error = dx + dy

    while True:
        if 0 <= y0 < len(grid) and 0 <= x0 < len(grid[y0]):
            grid[y0][x0] = mark
        if x0 == x1 and y0 == y1:
            return grid
        doubled = error * 2
        if doubled >= dy:
            error += dy
            x0 += step_x
        if doubled <= dx:
            error += dx
            y0 += step_y
