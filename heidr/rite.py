import random
from dataclasses import dataclass

from heidr import registry
from heidr.contracts import Context
from heidr.registry import Module

SEPARATOR = "//"


@dataclass(frozen=True)
class Rite:
    question: Module
    world: Module
    reading: Module
    silent: bool = False

    def __str__(self) -> str:
        names = [self.question.name, self.world.name, self.reading.name]
        return SEPARATOR.join(names) + (" (silent)" if self.silent else "")


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
