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
    defaults: dict[str, Any] = field(default_factory=dict)

    def available(self, ctx: Context) -> bool:
        if not set(self.needs) <= ctx.capabilities:
            return False
        probe = getattr(sys.modules.get(self.origin), "available", None)
        return True if probe is None else bool(probe(ctx))


@dataclass
class Visual:
    name: str
    event: str
    glyphs: str
    widget: Any
    origin: str


MODULES: dict[str, dict[str, Module]] = {slot: {} for slot in SLOTS}
VISUALS: dict[str, list[Visual]] = {}


def _register(slot: str, name: str, needs, visual: str, defaults):
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
            defaults=dict(defaults or {}),
        )
        return run

    return decorate


def question(name: str, *, needs=(), visual: str = "", defaults=None):
    return _register("question", name, needs, visual, defaults)


def world(name: str, *, needs=(), visual: str = "", defaults=None):
    return _register("world", name, needs, visual, defaults)


def reading(name: str, *, needs=(), visual: str = "", defaults=None):
    return _register("reading", name, needs, visual, defaults)


def visual(name: str, *, event: str, glyphs: str = "ascii"):
    if glyphs not in GLYPH_LEVELS:
        raise ValueError(f"{name} declares an unknown glyph level: {glyphs}")

    def decorate(widget):
        VISUALS.setdefault(name, []).append(
            Visual(name=name, event=event, glyphs=glyphs, widget=widget, origin=widget.__module__)
        )
        return widget

    return decorate


def usable(slot: str, ctx: Context) -> list[Module]:
    return [module for module in MODULES[slot].values() if module.available(ctx)]


def pick_visual(name: str, glyphs: str) -> Visual | None:
    # Choose the richest variant the terminal can actually draw.
    affordable = [v for v in VISUALS.get(name, []) if GLYPH_LEVELS.index(v.glyphs) <= GLYPH_LEVELS.index(glyphs)]
    return max(affordable, key=lambda v: GLYPH_LEVELS.index(v.glyphs), default=None)


def discover(user_dir: Path | None = None) -> None:
    for package in ("question", "world", "reading", "visuals"):
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
