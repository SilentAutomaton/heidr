import tomllib
from pathlib import Path

DEFAULTS: dict[str, dict[str, str]] = {
    "normal": {
        "colon": "command_line",
        "i": "ask",
        "h": "value_previous",
        "j": "line_down",
        "k": "line_up",
        "l": "value_next",
        "up": "line_up",
        "down": "line_down",
        "left": "value_previous",
        "right": "value_next",
        "pageup": "page_up",
        "pagedown": "page_down",
        "enter": "choose",
        "minus": "volume_down",
        "plus": "volume_up",
        "equals_sign": "volume_up",
        "m": "mute",
        "question_mark": "help",
        "escape": "stop",
    },
    "insert": {
        "escape": "normal_mode",
        "ctrl+v": "voice_input",
    },
    "leader": {
        "a": "ask",
        "d": "draw",
        "l": "ledger",
        "m": "modules",
        "s": "settings",
        "h": "checkhealth",
        "q": "quit",
    },
}

LEADER = "space"


def load(user_dir: Path | None = None) -> dict[str, dict[str, str]]:
    keymap = {section: dict(keys) for section, keys in DEFAULTS.items()}
    path = (user_dir / "keymap.toml") if user_dir else None
    if path is None or not path.is_file():
        return keymap
    with path.open("rb") as handle:
        overrides = tomllib.load(handle)
    for section, keys in overrides.items():
        if section in keymap and isinstance(keys, dict):
            keymap[section].update(keys)
    return keymap


def leader_key(user_dir: Path | None = None) -> str:
    path = (user_dir / "keymap.toml") if user_dir else None
    if path is None or not path.is_file():
        return LEADER
    with path.open("rb") as handle:
        return tomllib.load(handle).get("leader", LEADER)
