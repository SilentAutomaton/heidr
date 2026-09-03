from heidr.registry import animation
from heidr.visuals.canvas import Frame
from heidr.visuals.paint import blank, lines

# Fumes rising from a tripod. Shown while the pythia reading is at work, which
# is the one reading that asks a model to interpret rather than to invent, and
# is named for the woman who sat over the cleft at Delphi and breathed whatever
# came out of it.
#
# The plume is value noise carried upward and spread as it climbs: hashed from
# the cell and the frame rather than drawn from a generator, so a repaint of one
# tick gives the same screen.
STEM = 3
RISE = 0.7
SPREAD = 0.16
QUIET = 1.7


def hashed(x: int, y: int) -> float:
    mixed = (x * 73856093) ^ (y * 19349663)
    return (mixed % 1000) / 1000


def paint(frame: Frame) -> list[str]:
    grid = blank(frame.width, frame.height)
    ground = frame.height - 1
    middle = frame.width // 2
    top = frame.ramp[-1]

    # The tripod: three legs and a bowl, drawn once and never moving.
    for offset in (-3, 0, 3):
        for row in range(STEM):
            if 0 <= ground - row < frame.height:
                grid[ground - row][middle + offset] = frame.ramp[len(frame.ramp) // 2]
    for offset in range(-4, 5):
        grid[ground - STEM][middle + offset] = top

    for row in range(ground - STEM):
        height = ground - STEM - row
        width = max(1, int(height * SPREAD * frame.width / 8))
        drift = int(hashed(height, 0) * 3) - 1
        for column in range(middle - width + drift, middle + width + drift + 1):
            if not 0 <= column < frame.width:
                continue
            noise = hashed(column * 3 - int(height * 1.7), height - int(frame.tick * RISE))
            thin = 1 - abs(column - middle - drift) / (width + 1)
            level = (noise * thin * (1 - height / max(1, ground))) ** QUIET
            step = round(level * (len(frame.ramp) - 1) * 2.6)
            if step > 0:
                grid[row][column] = frame.ramp[min(len(frame.ramp) - 1, step)]
    return lines(grid)


for level in ("ascii", "blocks", "braille"):
    animation("vapour", glyphs=level, fps=10)(paint)
