from heidr import registry
from heidr.config import DEFAULTS

CURSOR = "> "
BLANK = "  "

# The way in. Every entry names the action it runs, the command that runs the
# same thing, and the key that runs it without the command line: modal control
# is shown rather than hidden.
ENTRIES = (
    ("ask", "ask a question", ":ask", "{leader}a"),
    ("ledger", "past draws", ":ledger", "{leader}l"),
    ("modules", "modules", ":modules", "{leader}m"),
    ("settings", "settings", ":settings", "{leader}s"),
    ("checkhealth", "health", ":checkhealth", "{leader}h"),
    ("help", "help", ":help", "?"),
    ("quit", "leave", ":q", "{leader}q"),
)


def menu_rows(leader: str) -> list[tuple[str, str]]:
    rows = []
    for action, label, command, key in ENTRIES:
        keys = key.format(leader=f"<{leader}>")
        rows.append((action, f"{label:<16} {command:<14} {keys}"))
    return rows


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
        for name in values:
            dotted = f"{section}.{name}"
            rows.append((dotted, _setting_line(dotted, config.get(dotted))))
    # A module declares its own options, so they are read from the module and
    # not from the defaults table. Switching a module off is not among them: it
    # is the whole of the module list, and one switch in two places is two
    # truths.
    for slot in registry.SLOTS:
        for name, module in sorted(registry.MODULES[slot].items()):
            values = config.module(name, module.defaults)
            for option in sorted(module.defaults):
                dotted = f"modules.{name}.{option}"
                rows.append((dotted, _setting_line(dotted, values.get(option))))
    return rows


def _setting_line(dotted: str, value) -> str:
    return f"{dotted:<34} {value}"


def ledger_rows(ledger) -> list[tuple[str, str]]:
    """Past draws, newest last, the way the files sit on disk."""
    rows = []
    for entry in ledger.entries():
        date = entry.get("Date")[:16].replace("T", " ")
        rite = entry.get("Rite") or "-"
        rows.append((entry.identifier, f"{entry.identifier}  {date}  {entry.get('Status'):<8} {rite}"))
    return rows


def window(count: int, cursor: int, height: int) -> tuple[int, int]:
    """The slice of a long list that keeps the cursor on screen."""
    if height <= 0 or count <= height:
        return 0, count
    start = min(max(cursor - height // 2, 0), count - height)
    return start, start + height


def render(rows: list[tuple[str, str]], cursor: int, empty: str, height: int = 0) -> str:
    if not rows:
        return empty

    start, end = window(len(rows), cursor, height)
    lines = []
    for index in range(start, end):
        lines.append((CURSOR if index == cursor else BLANK) + rows[index][1])
    if end < len(rows) or start > 0:
        lines.append(f"  {start + 1}-{end} of {len(rows)}")
    return "\n".join(lines)
