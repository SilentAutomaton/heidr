from heidr.visuals.art.seeress import figure
from heidr.visuals.paint import ASCII

# The corners are the only part that needs a richer terminal; everything else
# here is plain ASCII, so the field looks the same in a console.
ROUND = ("╭", "╮", "╰", "╯", "─", "│")
PLAIN = ("+", "+", "+", "+", "-", "|")
CARET = "_"
GAP = "  "
NARROWEST = 12
WIDEST = 56
# Below this the figure and the field cannot both fit, and a field cut in half
# is worse than no figure at all.
ROOM_FOR_HER = 74


def field(typed: str, width: int, glyphs: str) -> list[str]:
    """A box with the question in it, scrolled to keep the end in view."""
    left, right, bottom_left, bottom_right, across, down = PLAIN if glyphs == "ascii" else ROUND
    inside = max(NARROWEST, width) - 2
    shown = (typed + CARET)[-(inside - 2):]
    return [
        left + across * inside + right,
        down + " " + shown.ljust(inside - 1) + down,
        bottom_left + across * inside + bottom_right,
    ]


def beside(left: list[str], right: list[str]) -> list[str]:
    pad = " " * max(len(line) for line in left)
    rows = []
    for number in range(max(len(left), len(right))):
        here = left[number] if number < len(left) else pad
        there = right[number] if number < len(right) else ""
        rows.append((here.ljust(len(pad)) + GAP + there).rstrip())
    return rows


def panel(typed: str, tick: int, width: int, glyphs: str, hint: str) -> str:
    """Heiðr waits on the left, the question is typed on the right."""
    drawn = figure(tick, ASCII)
    if width < ROOM_FOR_HER:
        return "\n".join(field(typed, min(WIDEST, width), glyphs) + ["", hint])
    room = min(WIDEST, width - len(drawn[0]) - len(GAP))
    return "\n".join(beside(drawn, field(typed, room, glyphs) + ["", hint]))
