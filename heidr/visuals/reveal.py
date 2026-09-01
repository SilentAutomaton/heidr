import random

from heidr.registry import visual
from heidr.visuals.base import Visualisation

# Text arrives looking like noise and resolves character by character. The
# mechanic is the one from no-more-secrets by Brian Barto, GPL-3.0, where the
# reveal waits for the reader rather than happening at them.
# https://github.com/bartobri/no-more-secrets
NOISE = "!@#$%^&*()_+-=[]{};:,.<>/?\\|~abcdefghijklmnopqrstuvwxyz0123456789"
SETTLE = 0.06


def scramble(target: str, resolved: set[int], rng: random.Random) -> str:
    return "".join(
        character if index in resolved or character in " \n" else rng.choice(NOISE)
        for index, character in enumerate(target)
    )


def next_resolved(count: int, resolved: set[int], share: float, rng: random.Random) -> set[int]:
    remaining = [index for index in range(count) if index not in resolved]
    if not remaining:
        return resolved
    taking = max(1, int(len(remaining) * share))
    return resolved | set(rng.sample(remaining, min(taking, len(remaining))))


@visual("reveal", event="token", glyphs="ascii")
class Reveal(Visualisation):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.target = ""
        self.resolved: set[int] = set()
        self.rng = random.Random()

    def on_mount(self) -> None:
        self.set_interval(SETTLE, self.step)

    def feed(self, token: str) -> None:
        self.target = f"{self.target}\n{token}".strip()
        self.refresh()

    def settled(self) -> bool:
        return len(self.resolved) >= len(self.target)

    def step(self) -> None:
        if self.settled():
            return
        self.resolved = next_resolved(len(self.target), self.resolved, 0.12, self.rng)
        self.refresh()

    def render(self) -> str:
        if not self.target:
            return ""
        return scramble(self.target, self.resolved, self.rng)
