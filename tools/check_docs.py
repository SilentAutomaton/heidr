"""Every module must be documented in both languages, with the same sections.

Run it directly, or let the test suite run it. It exists so documentation
cannot quietly fall behind the code: a module with no document fails the build
the same way a broken test does.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from heidr import registry  # noqa: E402

REQUIRED = {
    "en": ("What it does", "Where the data comes from", "How it is processed", "Dependencies", "Sources"),
    "ru": ("Что делает", "Откуда берутся данные", "Как обрабатывается", "Зависимости", "Источники"),
}


def module_names() -> list[str]:
    return sorted(name for slot in registry.SLOTS for name in registry.MODULES[slot])


def complaints() -> list[str]:
    found = []
    for name in module_names():
        for language, sections in REQUIRED.items():
            path = ROOT / "docs" / language / "modules" / f"{name}.md"
            if not path.is_file():
                found.append(f"{name}: no {language} document at {path.relative_to(ROOT)}")
                continue
            text = path.read_text(encoding="utf-8")
            missing = [section for section in sections if f"## {section}" not in text]
            if missing:
                found.append(f"{name} ({language}): missing sections {', '.join(missing)}")
    return found


def main() -> int:
    found = complaints()
    for line in found:
        print(line)
    print(f"{len(module_names())} modules, {len(found)} complaints")
    return 1 if found else 0


if __name__ == "__main__":
    registry.discover()
    sys.exit(main())
