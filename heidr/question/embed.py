import hashlib
from urllib.parse import urlparse

from heidr import net
from heidr.contracts import Key
from heidr.question.words import digest_seed, words
from heidr.registry import question

MODEL = "nomic-embed-text"


def available(ctx) -> bool:
    # Embeddings are asked of ollama directly; the chat providers do not offer
    # them, so this rite waits for a local daemon.
    return ctx.llm is not None and ctx.llm.name == "ollama"


def embedding(base_url: str, model: str, text: str, timeout: float) -> list[float]:
    return net.post_json(
        f"{base_url.rstrip('/')}/api/embeddings",
        {"model": model, "prompt": text},
        timeout=timeout,
    ).get("embedding", [])


def fold(vector: list[float]) -> int:
    """Turn a vector into one number.

    An embedding is a direction in several hundred dimensions, not a quantity,
    so there is nothing meaningful to add up. It is hashed instead: the same
    question always lands in the same place, and near-identical questions do
    not, which is the property the rite needs.
    """
    if not vector:
        return 0
    packed = ",".join(f"{value:.6f}" for value in vector[:64]).encode()
    return int.from_bytes(hashlib.sha256(packed).digest(), "big")


@question("embed", visual="lattice", needs=("llm",), defaults={"model": MODEL, "timeout": 20})
def run(ctx, text: str) -> Key:
    base_url = ctx.config.get("llm.base_url", "http://localhost:11434")
    if not urlparse(base_url).hostname:
        return Key(seed=digest_seed(text))

    vector = embedding(base_url, ctx.settings["model"], text, float(ctx.settings["timeout"]))
    seed = fold(vector) or digest_seed(text)
    return Key(seed=seed, anchors=tuple(words(text)[:2]))
