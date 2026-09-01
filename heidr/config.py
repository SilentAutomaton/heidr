import os
import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import tomli_w

DEFAULTS: dict[str, Any] = {
    "ui": {"theme": "auto", "language": "en", "splash": True, "motion": True},
    "audio": {
        "volume": 0.6,
        "target_rms": 0.12,
        "limiter_ceiling": 0.95,
        "attack_ms": 50,
        "release_ms": 400,
    },
    "llm": {
        "provider": "ollama",
        "model": "qwen3.5:9B",
        "base_url": "http://localhost:11434",
        "api_key_env": "HEIDR_LLM_KEY",
        "think": False,
    },
    "stt": {
        "provider": "vosk",
        "model_path": "",
        "api_key_env": "HEIDR_STT_KEY",
        "language": "auto",
        "window_s": 30,
        "threads": 0,
        "binary": "",
    },
    "rite": {"silence_chance": 0.125, "recent_penalty": 4},
    "ledger": {"path": "~/.local/share/heidr/ledger"},
    "history": {"path": "~/.local/share/heidr"},
    "modules": {},
}

SYSTEM_DIR = Path("/etc/heidr")
USER_DIR = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser() / "heidr"
EXAMPLE = Path(__file__).resolve().parent.parent / "config.example.toml"


@dataclass
class Config:
    data: dict[str, Any] = field(default_factory=dict)
    path: Path | None = None

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def set(self, dotted: str, value: Any) -> None:
        parts = dotted.split(".")
        node = self.data
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def module(self, name: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
        return merge(defaults or {}, self.get(f"modules.{name}", {}))

    def secret(self, dotted: str) -> str:
        return os.environ.get(self.get(dotted, ""), "")


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    # Nested dicts are copied, not shared, so a loaded config can never write
    # back into DEFAULTS.
    result: dict[str, Any] = {
        key: merge(value, {}) if isinstance(value, dict) else value
        for key, value in base.items()
    }
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value
    return result


def read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load(user_dir: Path | None = None, system_dir: Path | None = None) -> Config:
    user_dir = user_dir or USER_DIR
    system_dir = system_dir or SYSTEM_DIR
    data = merge(DEFAULTS, read(system_dir / "config.toml"))
    data = merge(data, read(user_dir / "config.toml"))
    return Config(data, user_dir / "config.toml")


def differences(data: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, dict):
            nested = differences(value, base.get(key, {}) if isinstance(base.get(key), dict) else {})
            if nested:
                result[key] = nested
        elif base.get(key) != value:
            result[key] = value
    return result


def save(config: Config) -> Path:
    path = config.path or (USER_DIR / "config.toml")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        tomli_w.dump(differences(config.data, DEFAULTS), handle)
    return path


def install_example(user_dir: Path | None = None) -> Path | None:
    user_dir = user_dir or USER_DIR
    target = user_dir / "config.toml"
    if target.exists() or not EXAMPLE.is_file():
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(EXAMPLE, target)
    return target
