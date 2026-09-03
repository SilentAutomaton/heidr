import random
from dataclasses import dataclass
from itertools import groupby
from typing import Any

from rich.text import Text
from textual.widgets import Static

from heidr.visuals.paint import ASCII

DEFAULT_FPS = 8


@dataclass(frozen=True)
class Frame:
    """Everything an animation is allowed to know.

    Geometry arrives on every frame and is never remembered, which is why the
    terminal can be resized mid capture and nothing notices.
    """

    width: int
    height: int
    tick: int
    ramp: str
    glyphs: str
    payload: Any = None


class Painter:
    """One animation. Paint a frame; take an event if you want one."""

    ramp = ASCII

    def paint(self, frame: Frame) -> list[str]:
        raise NotImplementedError

    def feed(self, payload: Any) -> None:
        pass


class Drawn(Painter):
    """A painter written as a plain function, which most of them are."""

    def __init__(self, draw, ramp: str):
        self.draw = draw
        self.ramp = ramp
        self.payload: Any = None

    def paint(self, frame: Frame) -> list[str]:
        return self.draw(frame)

    def feed(self, payload: Any) -> None:
        self.payload = payload


class Canvas(Static):
    """The one widget that shows animations, whichever one is running."""

    def __init__(self, glyphs: str = "ascii", **kwargs):
        super().__init__(**kwargs)
        self.glyphs = glyphs
        self.painter: Painter | None = None
        # One colour per level of the ramp, for the animations that draw
        # something measured. Empty means the widget's own colour, flat.
        self.tint: tuple[str, ...] = ()
        self.tick = 0
        self.timer = None
        self.rng = random.Random()

    def show(self, painter: Painter | None, fps: int = DEFAULT_FPS, tint=()) -> None:
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        self.painter = painter
        self.tint = tuple(tint)
        self.tick = 0
        if painter is not None:
            self.timer = self.set_interval(1 / max(1, fps), self.advance)
        self.refresh()

    def advance(self) -> None:
        self.tick += 1
        self.refresh()

    def feed(self, payload: Any) -> None:
        if self.painter is not None:
            self.painter.feed(payload)
            self.refresh()

    def render(self) -> str | Text:
        width, height = self.size.width, self.size.height
        if self.painter is None or width <= 0 or height <= 0:
            return ""
        frame = Frame(
            width=width,
            height=height,
            tick=self.tick,
            ramp=self.painter.ramp,
            glyphs=self.glyphs,
            payload=getattr(self.painter, "payload", None),
        )
        drawn = self.painter.paint(frame)[:height]
        if len(self.tint) > 1:
            return shaded(drawn, frame.ramp, self.tint)
        return "\n".join(drawn)


def shaded(drawn: list[str], ramp: str, tint: tuple[str, ...]) -> Text:
    """Colour each character by how bright it is, in runs rather than in cells.

    A row of a waterfall is a few long stretches of one glyph, so a span per
    stretch is a few dozen spans where a span per cell would be a few thousand.

    Text is built rather than markup, because a painter is free to draw a square
    bracket and markup would read it as a tag.
    """
    text = Text()
    for number, line in enumerate(drawn):
        if number:
            text.append("\n")
        # Grouped by the colour rather than by the glyph, so two glyphs that
        # land on the same level of the gradient share one span.
        for colour, run in groupby(line, key=lambda mark: _level(mark, ramp, tint)):
            text.append("".join(run), style=colour)
    return text


def _level(character: str, ramp: str, tint: tuple[str, ...]) -> str:
    # A glyph the ramp does not contain — a letter, a line of a gear — is drawn
    # at full strength rather than left uncoloured.
    place = ramp.find(character)
    if place < 0:
        return tint[-1]
    return tint[place * (len(tint) - 1) // max(len(ramp) - 1, 1)]
