import hashlib
import random
from dataclasses import dataclass
from pathlib import Path

from heidr.contracts import Material
from heidr.registry import reading

CORPUS = Path(__file__).resolve().parent.parent / "data" / "hexagrams.txt"
STALKS = 49
OLD_YIN, YOUNG_YANG, YOUNG_YIN, OLD_YANG = 6, 7, 8, 9


@dataclass(frozen=True)
class Hexagram:
    number: int
    name: str
    gloss: str


def load(path: Path) -> dict[str, Hexagram]:
    found: dict[str, Hexagram] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        lines, number, name, gloss = line.split("|", 3)
        found[lines] = Hexagram(int(number), name, gloss)
    return found


def one_change(stalks: int, rng: random.Random) -> int:
    """One of the three handlings of the stalks, returning what is left.

    The heap is split, one stalk is taken from the right pile, and both piles
    are counted off in fours. Whatever the counting leaves is set aside. This is
    the Da Yan method, and it is the reason the four line values are not equally
    likely.
    """
    left = rng.randint(1, stalks - 1)
    right = stalks - left
    remainder_left = left % 4 or 4
    remainder_right = (right - 1) % 4 or 4
    return stalks - (1 + remainder_left + remainder_right)


def cast_line(rng: random.Random) -> int:
    stalks = STALKS
    for _ in range(3):
        stalks = one_change(stalks, rng)
    return stalks // 4


def cast(rng: random.Random) -> list[int]:
    return [cast_line(rng) for _ in range(6)]


def pattern(values: list[int]) -> str:
    return "".join("1" if value in (YOUNG_YANG, OLD_YANG) else "0" for value in values)


def moved(values: list[int]) -> str:
    # An old line is a line in the act of turning into its opposite.
    flipped = []
    for value in values:
        if value == OLD_YANG:
            flipped.append("0")
        elif value == OLD_YIN:
            flipped.append("1")
        else:
            flipped.append("1" if value == YOUNG_YANG else "0")
    return "".join(flipped)


def drawing(values: list[int]) -> list[str]:
    glyphs = {
        OLD_YIN: "-- --  x",
        YOUNG_YANG: "-----   ",
        YOUNG_YIN: "-- --   ",
        OLD_YANG: "-----   o",
    }
    return [glyphs[value] for value in reversed(values)]


@reading("iching", visual="hexagram", defaults={"corpus": ""})
def run(ctx, question: str, material: Material):
    book = load(Path(ctx.settings["corpus"]).expanduser() if ctx.settings["corpus"] else CORPUS)

    # The material decides the cast. The stalks are handled honestly, but the
    # hand that splits the heap is the world's, not a fresh coin toss.
    seed = hashlib.sha256(f"{material.source}{material.text}{material.numbers}".encode()).digest()
    values = cast(random.Random(int.from_bytes(seed, "big")))

    primary = book[pattern(values)]
    yield f"{primary.number}. {primary.name}"
    for line in drawing(values):
        yield line
    yield primary.gloss

    changing = [index + 1 for index, value in enumerate(values) if value in (OLD_YIN, OLD_YANG)]
    if not changing:
        return

    secondary = book[moved(values)]
    yield f"changing at {', '.join(str(place) for place in changing)}"
    yield f"{secondary.number}. {secondary.name}"
    yield secondary.gloss
