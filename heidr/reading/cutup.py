import random

from heidr.contracts import Material
from heidr.registry import reading

# The fold-in and straight cut are the two methods Burroughs and Gysin
# described. Parameterising the cut length follows zachng1/cutup.
METHODS = ("cut", "fold")


def straight_cut(words: list[str], size: int, rng: random.Random) -> list[str]:
    pieces = [words[start : start + size] for start in range(0, len(words), size)]
    rng.shuffle(pieces)
    return [" ".join(piece) for piece in pieces]


def fold_in(words: list[str], size: int, rng: random.Random) -> list[str]:
    half = len(words) // 2
    left = [words[start : start + size] for start in range(0, half, size)]
    right = [words[start : start + size] for start in range(half, len(words), size)]
    folded = []
    for index in range(max(len(left), len(right))):
        piece = (left[index] if index < len(left) else []) + (
            right[index] if index < len(right) else []
        )
        folded.append(" ".join(piece))
    return folded


@reading("cutup", defaults={"max_cut": 4, "lines": 6})
def run(ctx, question: str, material: Material):
    rng = random.Random(len(material.text) + len(question))
    words = material.text.split()
    if not words:
        return

    size = max(1, int(ctx.settings["max_cut"]))
    method = METHODS[rng.randrange(len(METHODS))]
    pieces = straight_cut(words, size, rng) if method == "cut" else fold_in(words, size, rng)

    for line in pieces[: int(ctx.settings["lines"])]:
        if line:
            yield line
