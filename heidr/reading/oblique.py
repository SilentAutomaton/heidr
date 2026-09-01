from pathlib import Path

from heidr.contracts import Material
from heidr.registry import reading

# A flat offline corpus, the way fortune keeps its files: the rite must never
# depend on a website answering. https://github.com/shlomif/fortune-mod
DECK = Path(__file__).resolve().parent.parent / "data" / "strategies.txt"


def load(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


@reading("oblique", visual="scissors", defaults={"deck": ""})
def run(ctx, question: str, material: Material):
    path = Path(ctx.settings["deck"]).expanduser() if ctx.settings["deck"] else DECK
    cards = load(path)
    if not cards:
        return
    index = (sum(material.numbers) + len(material.text)) % len(cards)
    yield cards[index]
