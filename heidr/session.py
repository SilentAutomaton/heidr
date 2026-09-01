from dataclasses import dataclass, field

from heidr import entropy, rite
from heidr.contracts import Context, Key, Material
from heidr.ledger import Entry, Ledger


class AlreadyAsked(Exception):
    def __init__(self, entry: Entry):
        super().__init__(entry.identifier)
        self.entry = entry


@dataclass
class Draw:
    entry: Entry
    rite: rite.Rite
    key: Key
    material: Material
    lines: list[str] = field(default_factory=list)

    def body(self) -> str:
        return body(self.material, self.lines)


def body(material: Material, lines: list[str]) -> str:
    parts = [material.text.strip(), "\n".join(lines)]
    return "\n\n".join(part for part in parts if part)


def perform(ctx: Context, ledger: Ledger, question: str) -> Draw:
    seen = ledger.asked_before(question)
    if seen is not None:
        raise AlreadyAsked(seen)

    # The promise is written before anything is drawn, so the answer cannot be
    # rolled again once it is known.
    entry = ledger.commit(question)
    try:
        drawn = rite.draw(
            ctx,
            seed=entropy.world_seed(entropy.collect(ctx)),
            recent=ledger.recent_modules(),
        )
        key, material, lines = _walk(ctx, drawn, question)
    except Exception:
        ledger.abandon(entry)
        raise

    ledger.complete(entry, str(drawn), question, body(material, lines))
    return Draw(entry, drawn, key, material, lines)


def _walk(ctx: Context, drawn: rite.Rite, question: str):
    ctx.emit("stage", drawn.question.name)
    key = drawn.question.run(_ready(ctx, drawn.question), question)

    ctx.emit("stage", drawn.world.name)
    material = drawn.world.run(_ready(ctx, drawn.world), key)

    lines: list[str] = []
    if drawn.silent:
        return key, material, lines

    ctx.emit("stage", drawn.reading.name)
    for line in drawn.reading.run(_ready(ctx, drawn.reading), question, material):
        lines.append(line)
        ctx.emit("token", line)
    return key, material, lines


def _ready(ctx: Context, module) -> Context:
    return ctx.for_module(module.name, module.defaults)
