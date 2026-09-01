from dataclasses import dataclass, field

from heidr import entropy, rite
from heidr.contracts import Cancelled, Context, Key, Material
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


def perform(ctx: Context, ledger: Ledger, question: str, spec: str = "") -> Draw:
    # A chosen rite is an experiment rather than a divination, so the same
    # question may be put to a different chain.
    if not spec:
        seen = ledger.asked_before(question)
        if seen is not None:
            raise AlreadyAsked(seen)

    # The promise is written before anything is drawn, so the answer cannot be
    # rolled again once it is known.
    entry = ledger.commit(question)
    material = None
    try:
        seed = entropy.world_seed(entropy.collect(ctx))
        recent = ledger.recent_modules()
        drawn = rite.chosen(ctx, spec, seed, recent) if spec else rite.draw(ctx, seed, recent)
        _still_wanted(ctx)
        ctx.emit("stage", drawn.question.name)
        key = drawn.question.run(_ready(ctx, drawn.question), question)

        _still_wanted(ctx)
        ctx.emit("stage", drawn.world.name)
        material = drawn.world.run(_ready(ctx, drawn.world), key)

        _still_wanted(ctx)
        lines = _read(ctx, drawn, question, material)
    except Exception:
        # Nothing was found, so the question is released. Once material exists
        # the question is spent, whatever happens next.
        ledger.abandon(entry, released=material is None)
        raise

    ledger.complete(entry, str(drawn), question, body(material, lines))
    return Draw(entry, drawn, key, material, lines)


def _still_wanted(ctx: Context) -> None:
    if ctx.cancelled():
        raise Cancelled


def _read(ctx: Context, drawn: rite.Rite, question: str, material: Material) -> list[str]:
    if drawn.silent:
        return []

    lines: list[str] = []
    ctx.emit("stage", drawn.reading.name)
    for line in drawn.reading.run(_ready(ctx, drawn.reading), question, material):
        lines.append(line)
        ctx.emit("token", line)
    return lines


def _ready(ctx: Context, module) -> Context:
    return ctx.for_module(module.name, module.defaults)
