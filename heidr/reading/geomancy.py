import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from heidr.contracts import Material
from heidr.registry import reading

TABLE = Path(__file__).resolve().parent.parent / "data" / "geomancy.txt"
ONE_POINT, TWO_POINTS = "  *", "* *"

Figure = tuple[int, int, int, int]


@dataclass(frozen=True)
class Meaning:
    name: str
    gloss: str


@dataclass(frozen=True)
class Shield:
    right: Figure
    left: Figure
    judge: Figure


def load(path: Path) -> dict[Figure, Meaning]:
    found: dict[Figure, Meaning] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        points, name, gloss = line.split("|", 2)
        found[tuple(int(point) for point in points)] = Meaning(name, gloss)
    return found


def add(first: Figure, second: Figure) -> Figure:
    return tuple(a ^ b for a, b in zip(first, second))


def raise_shield(mothers: list[Figure]) -> Shield:
    # The daughters read the mothers crosswise: heads, then necks, and so on.
    daughters = [tuple(mother[row] for mother in mothers) for row in range(4)]
    line = mothers + daughters
    nieces = [add(line[start], line[start + 1]) for start in range(0, 8, 2)]
    right, left = add(nieces[0], nieces[1]), add(nieces[2], nieces[3])
    return Shield(right, left, add(right, left))


def drawing(figure: Figure) -> list[str]:
    return [ONE_POINT if point else TWO_POINTS for point in figure]


@reading("geomancy", visual="hexagram")
def run(ctx, question: str, material: Material):
    meanings = load(TABLE)
    seed = hashlib.sha256(f"{material.source}{material.text}{material.numbers}".encode()).digest()
    rng = random.Random(int.from_bytes(seed, "big"))
    shield = raise_shield([tuple(rng.getrandbits(1) for _ in range(4)) for _ in range(4)])

    yield f"right witness: {meanings[shield.right].name}"
    yield f"left witness: {meanings[shield.left].name}"
    yield f"judge: {meanings[shield.judge].name}"
    for line in drawing(shield.judge):
        yield line
    yield meanings[shield.judge].gloss
