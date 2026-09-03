from heidr.contracts import Key
from heidr.question.words import digest_seed, rarity, words
from heidr.registry import question


@question("rarest", visual="zipf")
def run(ctx, text: str) -> Key:
    # One anchor, not two: the least ordinary word in the question is the one
    # worth looking for in what the world says back.
    found = words(text)
    if not found:
        return Key(seed=digest_seed(text))
    odd = max(found, key=rarity)
    return Key(seed=digest_seed(odd), anchors=(odd,))
