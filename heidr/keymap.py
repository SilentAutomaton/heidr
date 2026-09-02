import tomllib
from pathlib import Path

DEFAULTS: dict[str, dict[str, str]] = {
    "normal": {
        "colon": "command_line",
        # Six ways into insert, as in vim, all opening the one field there is.
        # The point is that the hand cannot miss.
        "i": "ask",
        "a": "ask",
        "A": "ask",
        "I": "ask",
        "o": "ask",
        "O": "ask",
        "h": "value_previous",
        "j": "line_down",
        "k": "line_up",
        "l": "value_next",
        "up": "line_up",
        "down": "line_down",
        # The second name for each of these is the one everybody else knows.
        # Nothing vim binds is taken away; a familiar key is put beside it.
        "tab": "line_down",
        "shift+tab": "line_up",
        "home": "first_line",
        "end": "last_line",
        "insert": "ask",
        "backspace": "back",
        "f1": "help",
        "f3": "search_next",
        "shift+f3": "search_previous",
        "ctrl+s": "write",
        "ctrl+z": "undo",
        "ctrl+y": "redo",
        "ctrl+c": "stop_or_quit",
        "left": "value_previous",
        "right": "value_next",
        "pageup": "page_up",
        "pagedown": "page_down",
        "ctrl+f": "page_down",
        "ctrl+b": "page_up",
        "ctrl+d": "half_page_down",
        "ctrl+u": "half_page_up",
        "G": "last_line",
        "left_curly_bracket": "section_up",
        "right_curly_bracket": "section_down",
        "ctrl+o": "back",
        "slash": "search",
        "n": "search_next",
        "N": "search_previous",
        "y": "yank",
        "u": "undo",
        "ctrl+r": "redo",
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
    # Two keys that wait for a second one, the way the leader does. In vim `g`
    # and `Z` are prefixes and nothing else, so they are prefixes here too.
    "g": {
        "g": "first_line",
    },
    "Z": {
        "Z": "write_and_quit",
        "Q": "quit",
    },
    "leader": {
        # Twice on the leader is the way home, wherever you are.
        "space": "menu",
        "a": "ask",
        "c": "compose",
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
