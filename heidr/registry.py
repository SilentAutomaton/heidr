import importlib
import importlib.util
import pkgutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from heidr.contracts import CAPABILITIES, Context

SLOTS = ("question", "world", "reading")
GLYPH_LEVELS = ("ascii", "box", "blocks", "braille")


@dataclass
class Module:
    name: str
    slot: str
    run: Callable
    origin: str
    needs: tuple[str, ...] = ()
    visual: str = ""
    # A reading that says nothing on purpose. Without this the rite cannot tell
    # a deliberate silence from a module that simply had no answer.
    silent: bool = False
    defaults: dict[str, Any] = field(default_factory=dict)

    def available(self, ctx: Context) -> bool:
        if not ctx.config.get(f"modules.{self.name}.enabled", True):
            return False
        if not set(self.needs) <= ctx.capabilities:
            return False
        probe = getattr(sys.modules.get(self.origin), "available", None)
        if probe is None:
            return True
        # The probe reads its own settings, so it gets the module scoped
        # context rather than the bare one.
        return bool(probe(ctx.for_module(self.name, self.defaults)))


@dataclass
class Animation:
    """One way of drawing something, at one glyph level."""

    name: str
    glyphs: str
    fps: int
    event: str
    make: Callable
    origin: str


MODULES: dict[str, dict[str, Module]] = {slot: {} for slot in SLOTS}
ANIMATIONS: dict[str, list[Animation]] = {}


def _register(slot: str, name: str, needs, visual: str, defaults, silent: bool = False):
    unknown = set(needs) - set(CAPABILITIES)
    if unknown:
        raise ValueError(f"{name} declares unknown capabilities: {sorted(unknown)}")

    def decorate(run: Callable) -> Callable:
        MODULES[slot][name] = Module(
            name=name,
            slot=slot,
            run=run,
            origin=run.__module__,
            needs=tuple(needs),
            visual=visual,
            silent=silent,
            defaults=dict(defaults or {}),
        )
        return run

    return decorate


def question(name: str, *, needs=(), visual: str = "", defaults=None):
    return _register("question", name, needs, visual, defaults)


def world(name: str, *, needs=(), visual: str = "", defaults=None):
    return _register("world", name, needs, visual, defaults)


def reading(name: str, *, needs=(), visual: str = "", defaults=None, silent: bool = False):
    return _register("reading", name, needs, visual, defaults, silent)


def animation(name: str, *, glyphs: str = "ascii", fps: int = 8, event: str = ""):
    """Register one animation. A function or a Painter subclass, either works."""
    if glyphs not in GLYPH_LEVELS:
        raise ValueError(f"{name} declares an unknown glyph level: {glyphs}")

    def decorate(drawn):
        ANIMATIONS.setdefault(name, []).append(
            Animation(
                name=name,
                glyphs=glyphs,
                fps=fps,
                event=event,
                make=_maker(drawn, glyphs),
                origin=drawn.__module__,
            )
        )
        return drawn

    return decorate


def _maker(drawn, glyphs: str) -> Callable:
    from heidr.visuals import paint
    from heidr.visuals.canvas import Drawn, Painter

    ramp = {"braille": paint.BRAILLE, "blocks": paint.BLOCKS}.get(glyphs, paint.ASCII)
    if isinstance(drawn, type) and issubclass(drawn, Painter):
        return drawn
    return lambda: Drawn(drawn, ramp)


def usable(slot: str, ctx: Context) -> list[Module]:
    return [module for module in MODULES[slot].values() if module.available(ctx)]


def pick_animation(name: str, glyphs: str) -> Animation | None:
    # Choose the richest variant the terminal can actually draw.
    level = GLYPH_LEVELS.index(glyphs)
    affordable = [a for a in ANIMATIONS.get(name, []) if GLYPH_LEVELS.index(a.glyphs) <= level]
    return max(affordable, key=lambda a: GLYPH_LEVELS.index(a.glyphs), default=None)


def discover(user_dir: Path | None = None) -> None:
    for package in ("question", "world", "reading", "visuals.art"):
        _import_package(f"heidr.{package}")
    if user_dir and user_dir.is_dir():
        for path in sorted(user_dir.glob("*.py")):
            _import_file(path)


def _import_package(dotted: str) -> None:
    package = importlib.import_module(dotted)
    for info in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{dotted}.{info.name}")


def _import_file(path: Path) -> None:
    name = f"heidr_user_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
