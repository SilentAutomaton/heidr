from heidr.contracts import Key
from heidr.llm import Message
from heidr.question.words import digest_seed, words
from heidr.registry import question

INSTRUCTION = (
    "Rewrite the question below as its opposite: same subject, same length, "
    "reversed intent. Answer with the rewritten question and nothing else."
)


def available(ctx) -> bool:
    return ctx.llm is not None


@question("reversal", visual="cog", needs=("llm",))
def run(ctx, text: str) -> Key:
    # The model rewrites the question, but it never chooses the answer. What it
    # produces is a key, and where that key leads is still the world's business.
    turned = "".join(
        ctx.llm.stream([Message("system", INSTRUCTION), Message("user", text)])
    ).strip()
    turned = turned or text
    return Key(seed=digest_seed(turned), anchors=tuple(words(turned)[:2]))
