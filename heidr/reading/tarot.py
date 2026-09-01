import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from heidr.contracts import Material
from heidr.registry import reading

DECK = Path(__file__).resolve().parent.parent / "data" / "tarot.txt"
SPREADS = {"one": ("the card",), "three": ("before", "now", "after")}
WIDTH = 18


@dataclass(frozen=True)
class Card:
    name: str
    upright: str
    reversed: str

    def meaning(self, upside_down: bool) -> str:
        return self.reversed if upside_down else self.upright


def load(path: Path) -> list[Card]:
    cards = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, upright, upside_down = line.split("|", 2)
        cards.append(Card(name, upright, upside_down))
    return cards


def frame(name: str, upside_down: bool) -> list[str]:
    # A card without borrowed art: a plain frame, and a mark when it is drawn
    # the other way up.
    mark = "reversed" if upside_down else ""
    return [
        "+" + "-" * WIDTH + "+",
        "|" + name[:WIDTH].center(WIDTH) + "|",
        "|" + mark.center(WIDTH) + "|",
        "+" + "-" * WIDTH + "+",
    ]


@reading("tarot", defaults={"deck": "", "spread": "three", "reversals": True})
def run(ctx, question: str, material: Material):
    cards = load(Path(ctx.settings["deck"]).expanduser() if ctx.settings["deck"] else DECK)
    places = SPREADS.get(ctx.settings["spread"], SPREADS["three"])

    seed = hashlib.sha256(f"{material.source}{material.text}{material.numbers}".encode()).digest()
    rng = random.Random(int.from_bytes(seed, "big"))
    drawn = rng.sample(cards, len(places))

    for place, card in zip(places, drawn):
        upside_down = bool(ctx.settings["reversals"]) and rng.random() < 0.5
        yield place
        for line in frame(card.name, upside_down):
            yield line
        yield card.meaning(upside_down)
