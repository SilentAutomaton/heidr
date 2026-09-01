import textwrap

from rich.text import Text

# The panel is centred and grows with what it holds, so it needs a limit of its
# own: a line of eighty characters is at the edge of comfortable reading, and a
# panel wider than that also leaves no room for the animation behind it.
WIDEST = 76
MARGIN = 4
INDENT = "  "
MATERIAL_LINES = 10
MARKER = "!"


def room(width: int) -> int:
    return max(20, min(WIDEST, width - MARGIN))


def wrap(body: str, width: int) -> list[str]:
    """Fold a block to the width, keeping the line breaks it already has.

    Long runs without spaces — base64, a wall of mojibake — are broken rather
    than left to run off the edge, which is what used to happen: the panel cut
    them and said nothing.
    """
    folded: list[str] = []
    for line in body.splitlines() or [""]:
        folded.extend(textwrap.wrap(line, width) or [""])
    return folded


def shorten(body: str, width: int, lines: int = MATERIAL_LINES) -> list[str]:
    """As much as fits, and an honest count of what is left over."""
    folded = wrap(body, width)
    if len(folded) <= lines:
        return folded
    kept = folded[:lines]
    shown = sum(len(line) for line in kept)
    return kept + [f"… {len(body) - shown} more characters"]


def section(label: str, note: str, body: list[str], dim: str) -> Text:
    """One labelled block: a quiet heading, then indented content."""
    out = Text()
    out.append(label, dim)
    if note:
        out.append(f" · {note}", dim)
    for line in body:
        out.append(f"\n{INDENT}{line}")
    return out


def notice(message: str, accent: str) -> Text:
    out = Text()
    out.append(f"{MARKER}  ", accent)
    out.append(message, accent)
    return out


def joined(parts: list[Text], gap: str = "\n\n") -> Text:
    out = Text()
    for number, part in enumerate(parts):
        if number:
            out.append(gap)
        out.append(part)
    return out
