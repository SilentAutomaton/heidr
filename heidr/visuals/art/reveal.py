import random

from heidr.registry import animation
from heidr.visuals.canvas import Frame, Painter

# Text arrives looking like noise and resolves character by character. The
# mechanic is the one from no-more-secrets by Brian Barto, GPL-3.0, where the
# reveal waits for the reader rather than happening at them.
# https://github.com/bartobri/no-more-secrets
NOISE = "!@#$%^&*()_+-=[]{};:,.<>/?\\|~abcdefghijklmnopqrstuvwxyz0123456789"
SHARE = 0.12


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


@animation("reveal", glyphs="ascii", fps=16, event="token")
class Reveal(Painter):
    def __init__(self):
        self.target = ""
        self.resolved: set[int] = set()
        self.rng = random.Random()
        self.last_tick = -1

    def feed(self, payload) -> None:
        self.target = f"{self.target}\n{payload}".strip()

    def settled(self) -> bool:
        return len(self.resolved) >= len(self.target)

    def paint(self, frame: Frame) -> list[str]:
        if not self.target:
            return []
        if frame.tick != self.last_tick and not self.settled():
            self.resolved = next_resolved(len(self.target), self.resolved, SHARE, self.rng)
            self.last_tick = frame.tick
        return scramble(self.target, self.resolved, self.rng).splitlines()
