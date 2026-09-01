from heidr import registry
from heidr.config import DEFAULTS

CURSOR = "> "
BLANK = "  "


def module_rows(ctx) -> list[tuple[str, str]]:
    """Every registered module, with the option key that switches it off."""
    rows = []
    for slot in registry.SLOTS:
        for name, module in sorted(registry.MODULES[slot].items()):
            rows.append((f"modules.{name}.enabled", _module_line(slot, name, module, ctx)))
    return rows


def _module_line(slot: str, name: str, module, ctx) -> str:
    if not enabled(ctx.config, name):
        state = "off"
    elif module.available(ctx):
        state = "ready"
    else:
        state = "needs " + ", ".join(module.needs) if module.needs else "unavailable"
    return f"{slot:<9} {name:<14} {state}"


def enabled(config, name: str) -> bool:
    return bool(config.get(f"modules.{name}.enabled", True))


def setting_rows(config) -> list[tuple[str, str]]:
    """The configurable options, one per line, deepest key last."""
    rows = []
    for section, values in DEFAULTS.items():
        if section == "modules":
            continue
        for key in values:
            dotted = f"{section}.{key}"
            rows.append((dotted, f"{dotted:<24} {config.get(dotted)}"))
    return rows


def render(rows: list[tuple[str, str]], cursor: int, empty: str) -> str:
    if not rows:
        return empty
    lines = []
    for index, (_key, line) in enumerate(rows):
        lines.append((CURSOR if index == cursor else BLANK) + line)
    return "\n".join(lines)
