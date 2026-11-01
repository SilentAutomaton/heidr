from pathlib import Path

from heidr.contracts import Key, Material
from heidr.registry import world

BOOK = Path(__file__).resolve().parent.parent / "data" / "edda.txt"


def passages(text: str) -> list[str]:
    kept = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
    return [" ".join(block.split()) for block in kept.split("\n\n") if block.strip()]


@world("sortes", visual="hexlib", defaults={"book": ""})
def run(ctx, key: Key) -> Material:
    path = Path(ctx.settings["book"]).expanduser() if ctx.settings["book"] else BOOK
    found = passages(path.read_text(encoding="utf-8"))
    if not found:
        return Material("", (), path.stem, {"passages": 0})

    place = key.seed % len(found)
    ctx.emit("stage", f"sortes {path.stem} {place + 1}")
    return Material(
        text=found[place],
        numbers=(place + 1, len(found)),
        source=path.stem,
        extra={"passages": len(found)},
    )
