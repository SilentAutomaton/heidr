from dataclasses import dataclass, field, replace
from datetime import timedelta

from heidr import entropy, rite
from heidr.contracts import Cancelled, Context, Key, Material
from heidr.ledger import Entry, Ledger

ATTEMPTS = 3


class AlreadyAsked(Exception):
    def __init__(self, entry: Entry):
        super().__init__(entry.identifier)
        self.entry = entry


class NothingAnswered(Exception):
    """Every module of one slot was asked, and none of them had an answer.

    The last refusal is carried along: when the whole slot is exhausted, the
    reason the last one gave is the nearest thing to an explanation there is.
    """

    def __init__(self, slot: str, reason: str = ""):
        super().__init__(f"{slot}: {reason}" if reason else slot)
        self.slot = slot
        self.reason = reason


@dataclass
class Draw:
    entry: Entry
    rite: rite.Rite
    key: Key
    material: Material
    lines: list[str] = field(default_factory=list)
    instead: tuple[str, ...] = ()

    def body(self) -> str:
        return body(self.material, self.lines)


def body(material: Material, lines: list[str]) -> str:
    parts = [material.text.strip(), "\n".join(lines)]
    return "\n\n".join(part for part in parts if part)


def perform(ctx: Context, ledger: Ledger, question: str, spec: str = "") -> Draw:
    # A chosen rite is an experiment rather than a divination, so the same
    # question may be put to a different chain.
    if not spec:
        hours = float(ctx.config.get("ledger.repeat_after_h", 24))
        seen = ledger.asked_before(question, timedelta(hours=hours) if hours else None)
        if seen is not None:
            raise AlreadyAsked(seen)

    # The promise is written before anything is drawn, so the answer cannot be
    # rolled again once it is known.
    entry = ledger.commit(question)
    material = None
    gave_way: list[str] = []
    try:
        seed = entropy.world_seed(entropy.collect(ctx))
        recent = ledger.recent_modules()
        drawn = rite.chosen(ctx, spec, seed, recent) if spec else rite.draw(ctx, seed, recent)
        lots = Lots(ctx, seed, recent, max(1, int(ctx.config.get("rite.attempts", ATTEMPTS))))

        _still_wanted(ctx)
        module, key = lots.attempt("question", drawn.question, question, _is_key, gave_way)
        drawn = replace(drawn, question=module)

        _still_wanted(ctx)
        module, material = lots.attempt("world", drawn.world, key, _is_material, gave_way)
        drawn = replace(drawn, world=module)
        # The material is on screen as soon as it exists, not when the whole
        # rite is over: the reading can take a minute, and the reader has
        # something to look at meanwhile.
        ctx.emit("found", material)

        _still_wanted(ctx)
        drawn, lines = _read(lots, drawn, question, material, gave_way)
    except Exception:
        # The question is only spent when an answer really arrived, so a rite
        # that broke leaves it free whether or not material was found.
        ledger.abandon(entry, released=material is None, instead=tuple(gave_way))
        raise

    ledger.complete(entry, str(drawn), question, body(material, lines), tuple(gave_way))
    return Draw(entry, drawn, key, material, lines, tuple(gave_way))


@dataclass(frozen=True)
class Lots:
    """The lottery, kept open for the length of one rite.

    A module that cannot answer is a source gone quiet, not an answer somebody
    disliked, so drawing again in its place is not a second roll.
    """

    ctx: Context
    seed: int
    recent: tuple[str, ...]
    attempts: int

    def attempt(self, slot, first, argument, enough, gave_way):
        """Run one slot, and draw another module for it when it cannot answer.

        A refusal, a feed that will not parse, a source that returns nothing:
        from here they are one thing, a module with no answer today.
        """
        module = first
        avoid: set[str] = set()
        reason = ""
        for _ in range(self.attempts):
            self.ctx.emit("stage", module.name)
            try:
                value = module.run(_ready(self.ctx, module), argument)
            except Cancelled:
                raise
            except Exception as refusal:
                value, reason = None, _sentence(refusal)
            else:
                if enough(value):
                    return module, value
                reason = f"{module.name} found nothing."

            module = self.next_one(slot, module, avoid, gave_way)
            if module is None:
                break
        raise NothingAnswered(slot, reason)

    def next_one(self, slot, module, avoid, gave_way):
        avoid.add(module.name)
        gave_way.append(module.name)
        following = rite.instead(self.ctx, slot, avoid, self.seed, self.recent)
        if following is not None:
            self.ctx.emit("instead", (module.name, following.name))
        return following


def _sentence(failure: Exception) -> str:
    """A refusal, said the way a sentence is said.

    Module messages already end in a full stop; the text of a bare exception
    does not, and it is about to be read in the middle of a paragraph.
    """
    said = str(failure).strip() or failure.__class__.__name__
    return said if said.endswith((".", "!", "?")) else f"{said}."


def _is_key(key: Key) -> bool:
    return isinstance(key, Key)


def _is_material(material: Material) -> bool:
    # A source that answered with neither text nor numbers said nothing at all.
    return isinstance(material, Material) and bool(material.text.strip() or material.numbers)


def _still_wanted(ctx: Context) -> None:
    if ctx.cancelled():
        raise Cancelled


def _read(lots: Lots, drawn: rite.Rite, question: str, material: Material, gave_way):
    """The reading, which is the one slot that can fail halfway through a sentence."""
    if drawn.silent:
        return drawn, []

    module = drawn.reading
    avoid: set[str] = set()
    reason = ""
    for _ in range(lots.attempts):
        lots.ctx.emit("stage", module.name)
        lines, broke = _speak(lots.ctx, module, question, material)
        if isinstance(broke, Cancelled):
            raise broke
        if broke is not None:
            reason = _sentence(broke)
        # Whatever was already said is kept: running the reading again would
        # say it twice. Silence counts as an answer from a module that declares
        # silence to be the whole point of it.
        if lines or module.silent:
            return replace(drawn, reading=module), lines

        module = lots.next_one("reading", module, avoid, gave_way)
        if module is None:
            break
    raise NothingAnswered("reading", reason)


def _speak(ctx, module, question, material):
    lines: list[str] = []
    try:
        for line in module.run(_ready(ctx, module), question, material):
            lines.append(line)
            ctx.emit("token", line)
    except Exception as failure:
        return lines, failure
    return lines, None


def _ready(ctx: Context, module) -> Context:
    return ctx.for_module(module.name, module.defaults)
