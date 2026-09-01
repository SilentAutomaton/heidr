SEPARATOR = "  //  "
WAITING = "..."
SLOTS = 3
MARKS = {"ascii": (".", ">"), "box": ("·", ">"), "blocks": ("·", "▸")}


def marks(glyphs: str) -> tuple[str, str]:
    return MARKS.get(glyphs, MARKS["blocks"])


def bar(names: list[str], active: int, glyphs: str) -> str:
    """The three slots of the rite, with the one at work pointed at.

    A slot nobody has reached yet is named `...`: the rite is drawn one stage
    at a time, and pretending to know the next one would be a lie.
    """
    done, here = marks(glyphs)
    parts = []
    for slot in range(SLOTS):
        name = names[slot] if slot < len(names) else WAITING
        if slot == active:
            parts.append(f"{here} {name}")
        elif slot < len(names):
            parts.append(f"{done} {name}")
        else:
            parts.append(f"  {name}")
    return SEPARATOR.join(parts)
