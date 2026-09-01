from heidr.contracts import Key
from heidr.question.words import VOWELS, digest_seed, words
from heidr.registry import question


def consonants(word: str) -> str:
    return "".join(letter for letter in word if letter not in VOWELS)


@question("skeleton")
def run(ctx, text: str) -> Key:
    # Vowels carry grammar, consonants carry the root. Semitic writing left the
    # vowels out for a thousand years and lost nothing that mattered.
    bones = [consonants(word) for word in words(text)]
    bones = [bone for bone in bones if bone]
    return Key(seed=digest_seed(" ".join(bones)), anchors=tuple(bones[:2]))
