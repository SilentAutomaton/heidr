from heidr.contracts import Key
from heidr.question.words import digest_seed, words
from heidr.registry import question


@question("acrostic")
def run(ctx, text: str) -> Key:
    initials = "".join(word[0] for word in words(text))
    return Key(seed=digest_seed(initials), anchors=(initials,) if initials else ())
