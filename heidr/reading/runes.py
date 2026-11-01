import hashlib
import random
from pathlib import Path

from heidr.contracts import Material
from heidr.registry import reading

FUTHARK = Path(__file__).resolve().parent.parent / "data" / "futhark.txt"
NORNS = ("Urd", "Verdandi", "Skuld")


def load(path: Path) -> list[tuple[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        tuple(line.split("|", 1)) for line in lines if line.strip() and not line.startswith("#")
    ]


@reading("runes", visual="runes")
def run(ctx, question: str, material: Material):
    seed = hashlib.sha256(f"{material.source}{material.text}{material.numbers}".encode()).digest()
    rng = random.Random(int.from_bytes(seed, "big"))

    # Latin names only: a console font rarely has the Runic block.
    for norn, (name, gloss) in zip(NORNS, rng.sample(load(FUTHARK), len(NORNS))):
        yield norn
        yield name
        yield gloss
