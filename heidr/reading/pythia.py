import hashlib
import random

from heidr.contracts import Material
from heidr.llm import Message
from heidr.llm.base import lines
from heidr.registry import reading

# The voice is drawn too, so the same finding does not always get the same
# treatment. The list is deliberately short and deliberately mixed.
VOICES = (
    "a pythia: speak in short lines, never explain yourself",
    "a Roman augur: describe what the signs did, then what it meant to the state",
    "a Sufi teacher: answer with a question and one image",
    "a Zen teacher: two sentences at most, and no comfort",
    "a cartographer: describe the finding as terrain, and say which way is downhill",
    "an investigator: state the evidence, then the single most likely reading",
)

# The old wording told the model to use only what was in the fragment and to
# invent nothing. Handed a wall of random bytes, an honest model then answered
# that the fragment contains no actionable information — correct, and useless.
# An augur reading entrails knows they are entrails. What is asked for is a
# reading of a thing that was found, not a judgement on whether it is a message.
INSTRUCTION = (
    "You are {voice}. Below is a fragment of the world, picked up by machine: "
    "radio, a page of a library, a block of a chain, raw noise. It was not "
    "written for anyone and it is not a message. Above it is a question someone "
    "asked before it was found.\n\n"
    "Name one or two concrete things you notice in the fragment — a word, a "
    "shape, a repetition, a number — and say what they mean for the question. "
    "Speak as though the coincidence were meant.\n\n"
    "Never say that the fragment is random, meaningless or insufficient. Never "
    "explain what you are doing, and never mention yourself. Do not invent "
    "further findings beyond what is here. Answer in the same language and "
    "script as the question. At most six lines, no heading."
)
FRAGMENT_CHARS = 1200


def available(ctx) -> bool:
    return ctx.llm is not None


def voice_for(material: Material) -> str:
    seed = hashlib.sha256(f"{material.source}{material.text}".encode()).digest()
    return random.Random(int.from_bytes(seed, "big")).choice(VOICES)


def fragment(material: Material, limit: int) -> str:
    """As much of the finding as is worth reading, and an honest note if less.

    Four thousand random characters do not make a better reading than twelve
    hundred do; they make a worse one, and a slower.
    """
    body = material.text.strip()
    if len(body) > limit:
        body = f"{body[:limit]}\n(the first {limit} characters of {len(body)})"
    return f"source: {material.source}\nnumbers: {material.numbers}\n\n{body}"


@reading("pythia", visual="vapour", needs=("llm",))
def run(ctx, question: str, material: Material):
    voice = voice_for(material)
    limit = int(ctx.config.get("llm.fragment_chars", FRAGMENT_CHARS))

    # A reading yields lines, so the stream is put back together before it
    # leaves: otherwise the answer arrives one word per line.
    yield from lines(
        ctx.llm.stream(
            [
                Message("system", INSTRUCTION.format(voice=voice)),
                # The question is repeated at the end: a model follows the
                # last thing it read, and answering a Russian question in
                # English is the failure this prevents.
                Message(
                    "user",
                    f"question: {question}\n\nfound:\n{fragment(material, limit)}\n\n"
                    f"Now answer, in the language of this question: {question}",
                ),
            ]
        )
    )
