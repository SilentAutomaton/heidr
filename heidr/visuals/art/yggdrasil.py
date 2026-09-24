import math
from functools import cache

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter
from heidr.visuals.paint import ASCII, BLOCKS, blank, line, lines

# The ash Yggdrasil grows from the ground up, and at its roots the three Norns
# cut their runes, as the Völuspá has them doing at the well of Urðr. When the
# third rune is cut the tree rests, and then it grows again.
#
# The tree is a Lindenmayer system: a word rewritten by rules, then read as the
# moves of a pen. Lindenmayer published it in 1968 to describe how plants grow,
# and the rules are nobody's. The branches are cut with the same four strokes
# as the wordmark, so tree and name look carved by one hand.
AXIOM = "X"
RULES = {"X": "F[+X][-X]F[+X][-X]X", "F": "FF"}
GENERATIONS = 3
TURN = math.radians(40)
GROW = 2
CUT = 6
HOLD = 40
# Urðr, Verðandi, Skuld: what was, what is becoming, what shall be. In a
# console without runes their initials stand in.
NORNS = {"ascii": "UVS", "blocks": "ᚢᚹᛊ"}


@cache
def branches() -> tuple[tuple[float, float, float, float, int], ...]:
    """Every stroke of the tree, with how far from the root it is.

    The distance is what makes it grow like a tree rather than like a pen: all
    the branches of one height appear together.
    """
    word = AXIOM
    for _ in range(GENERATIONS):
        word = "".join(RULES.get(letter, letter) for letter in word)

    x, y, heading, depth = 0.0, 0.0, math.pi / 2, 0
    stack, strokes = [], []
    for letter in word:
        if letter == "F":
            nx, ny = x + math.cos(heading), y + math.sin(heading)
            strokes.append((x, y, nx, ny, depth))
            x, y, depth = nx, ny, depth + 1
        elif letter == "+":
            heading -= TURN
        elif letter == "-":
            heading += TURN
        elif letter == "[":
            stack.append((x, y, heading, depth))
        elif letter == "]":
            x, y, heading, depth = stack.pop()
    return tuple(strokes)


def stroke(dx: float, dy: float) -> str:
    """The carved mark for a direction: a stave, a slant, or a flat cut."""
    angle = math.degrees(math.atan2(dy, dx)) % 180
    if angle < 22 or angle > 158:
        return "_"
    if angle < 68:
        return "/"
    if angle > 112:
        return "\\"
    return "|"


class Yggdrasil(Painter):
    ramp = ASCII
    glyphs = "ascii"

    def paint(self, frame: Frame) -> list[str]:
        grid = blank(frame.width, frame.height)
        if frame.width < 8 or frame.height < 5:
            return lines(grid)

        strokes = branches()
        tallest = max(depth for *_, depth in strokes) + 1
        cycle = tallest * GROW + len(NORNS[self.glyphs]) * CUT + HOLD
        age = frame.tick % cycle
        grown = age // GROW

        # The crown is stretched to the whole width and the whole height. The
        # panel covers the middle of the screen, so a tree kept to its true
        # shape would be all trunk behind it; stretched, its branches reach
        # the edges and its roots run below the panel, where they are seen.
        left = min(x for x, _, nx, _, _ in strokes for x in (x, nx))
        right = max(x for x, _, nx, _, _ in strokes for x in (x, nx))
        top = max(y for _, y, _, ny, _ in strokes for y in (y, ny))
        ground = frame.height - 3
        across = (frame.width - 2) / (right - left)
        up = (ground - 1) / top
        middle = frame.width // 2

        def cell(x: float, y: float) -> tuple[int, int]:
            return middle + round(x * across), ground - round(y * up)

        for x, y, nx, ny, depth in strokes:
            if depth > grown:
                continue
            (x0, y0), (x1, y1) = cell(x, y), cell(nx, ny)
            # The stroke follows the branch as grown, not as stretched: a
            # stretched crown would be cut in flat marks only.
            line(grid, x0, y0, x1, y1, stroke(nx - x, ny - y))

        # Three roots, and a Norn's rune at the end of each once the crown is
        # full. They are cut one after another, as the stanza tells it.
        norns = NORNS[self.glyphs]
        cut = max(0, min(len(norns), (age - tallest * GROW) // CUT + 1)) if grown >= tallest else 0
        reach = 2 * (frame.height - 1 - ground)
        for number, (dx, mark) in enumerate(((-reach, "/"), (0, "|"), (reach, "\\"))):
            end = (middle + dx, frame.height - 1)
            line(grid, middle, ground + 1, end[0], end[1], mark)
            if number < cut:
                grid[end[1]][max(0, min(frame.width - 1, end[0]))] = norns[number]
        return lines(grid)


@animation("yggdrasil", glyphs="ascii", fps=8)
class PlainYggdrasil(Yggdrasil):
    pass


@animation("yggdrasil", glyphs="blocks", fps=8)
class RunicYggdrasil(Yggdrasil):
    ramp = BLOCKS
    glyphs = "blocks"
