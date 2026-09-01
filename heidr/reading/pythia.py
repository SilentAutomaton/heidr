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

INSTRUCTION = (
    "You are {voice}. Below is a fragment found in the physical world, and a "
    "question someone asked before it was found. Read the fragment as an answer "
    "to the question. Use only what is in the fragment. Do not invent further "
    "findings, do not hedge, and do not mention that you are a model. "
    "At most six lines."
)


def available(ctx) -> bool:
    return ctx.llm is not None


def voice_for(material: Material) -> str:
    seed = hashlib.sha256(f"{material.source}{material.text}".encode()).digest()
    return random.Random(int.from_bytes(seed, "big")).choice(VOICES)


@reading("pythia", visual="cog", needs=("llm",))
def run(ctx, question: str, material: Material):
    voice = voice_for(material)
    found = f"source: {material.source}\nnumbers: {material.numbers}\n\n{material.text}"

    # A reading yields lines, so the stream is put back together before it
    # leaves: otherwise the answer arrives one word per line.
    yield from lines(
        ctx.llm.stream(
            [
                Message("system", INSTRUCTION.format(voice=voice)),
                Message("user", f"question: {question}\n\nfound:\n{found}"),
            ]
        )
    )
