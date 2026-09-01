from heidr.contracts import Key
from heidr.registry import question


@question("blind", visual="plasma")
def run(ctx, text: str) -> Key:
    # Double blind: the words are discarded and only the shape of the question
    # survives, so nothing you wrote can steer where the answer comes from.
    return Key(seed=len(text) * 2654435761, anchors=())
