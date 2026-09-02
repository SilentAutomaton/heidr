import random
from dataclasses import dataclass

from heidr import registry
from heidr.contracts import Context, Unavailable
from heidr.registry import Module

SEPARATOR = "//"
LOTTERY = ("*", "")


@dataclass(frozen=True)
class Rite:
    question: Module
    world: Module
    reading: Module
    silent: bool = False
    chosen: bool = False

    def __str__(self) -> str:
        line = SEPARATOR.join([self.question.name, self.world.name, self.reading.name])
        if self.chosen:
            line += " (chosen)"
        if self.silent:
            line += " (silent)"
        return line


class NothingAvailable(Exception):
    pass


def weights(modules: list[Module], recent: tuple[str, ...], penalty: int) -> list[float]:
    # Modules drawn recently are penalised, not banned: a repeat has to stay
    # possible, or a coincidence would mean nothing.
    return [1 / penalty if module.name in recent else 1.0 for module in modules]


def pick(modules: list[Module], recent: tuple[str, ...], penalty: int, rng: random.Random) -> Module:
    if not modules:
        raise NothingAvailable
    return rng.choices(modules, weights=weights(modules, recent, penalty))[0]


def draw(ctx: Context, seed: int, recent: tuple[str, ...] = ()) -> Rite:
    rng = random.Random(seed)
    penalty = max(1, int(ctx.config.get("rite.recent_penalty", 4)))
    chance = float(ctx.config.get("rite.silence_chance", 0.125))
    return Rite(
        question=pick(registry.usable("question", ctx), recent, penalty, rng),
        world=pick(registry.usable("world", ctx), recent, penalty, rng),
        reading=pick(registry.usable("reading", ctx), recent, penalty, rng),
        silent=rng.random() < chance,
    )


def instead(ctx: Context, slot: str, avoid: set[str], seed: int, recent: tuple[str, ...] = ()):
    """Another module for this slot, from the same lottery minus the failures.

    A module that cannot answer is a source gone quiet, not an answer somebody
    disliked, so drawing again in its place is not a second roll. What was tried
    is written into the entry, and the rite says who really spoke.
    """
    left = [module for module in registry.usable(slot, ctx) if module.name not in avoid]
    if not left:
        return None
    penalty = max(1, int(ctx.config.get("rite.recent_penalty", 4)))
    return pick(left, recent, penalty, random.Random(seed + len(avoid)))


def named(ctx: Context, slot: str, name: str) -> Module:
    """One module by name, or a refusal that says what the names are."""
    found = registry.MODULES[slot].get(name)
    if found is None:
        offered = ", ".join(sorted(registry.MODULES[slot]))
        raise Unavailable(f"There is no {slot} called {name!r}. The {slot} modules are: {offered}.")
    if found not in registry.usable(slot, ctx):
        raise Unavailable(f"{name} cannot run here. Run :checkhealth to see what it needs.")
    return found


def chosen(ctx: Context, spec: str, seed: int, recent: tuple[str, ...] = ()) -> Rite:
    """A rite named rather than drawn: three names separated by //.

    A slot given as `*`, or left empty, is drawn as usual. A rite that was
    chosen is marked as chosen wherever it is shown, because a coincidence
    somebody picked is not a coincidence.
    """
    wanted = [part.strip() for part in spec.split(SEPARATOR)]
    if len(wanted) != len(registry.SLOTS):
        raise Unavailable("A rite is three names separated by //, as in rarest//babel//iching.")

    rng = random.Random(seed)
    penalty = max(1, int(ctx.config.get("rite.recent_penalty", 4)))
    chance = float(ctx.config.get("rite.silence_chance", 0.125))
    picked = {}
    for slot, name in zip(registry.SLOTS, wanted):
        # The lottery still runs for the slots nobody named, out of the same
        # seed, so a half chosen rite is half a coincidence.
        picked[slot] = (
            pick(registry.usable(slot, ctx), recent, penalty, rng)
            if name in LOTTERY
            else named(ctx, slot, name)
        )

    # A named reading is a reading somebody wants to hear, so it is not silenced.
    silent = wanted[-1] in LOTTERY and rng.random() < chance
    return Rite(**picked, silent=silent, chosen=True)
