import random
from dataclasses import dataclass
from typing import Any

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
        self.tick = 0
        self.timer = None
        self.rng = random.Random()

    def show(self, painter: Painter | None, fps: int = DEFAULT_FPS) -> None:
        if self.timer is not None:
            self.timer.stop()
            self.timer = None
        self.painter = painter
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

    def render(self) -> str:
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
        return "\n".join(self.painter.paint(frame)[:height])
