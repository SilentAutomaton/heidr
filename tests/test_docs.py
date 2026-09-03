import subprocess
import sys
from pathlib import Path

from tools.check_docs import complaints, module_names

ROOT = Path(__file__).resolve().parent.parent


def test_every_module_is_documented_in_both_languages():
    found = complaints()

    assert found == [], "\n".join(found)


def test_the_documentation_folders_mirror_each_other():
    english = {path.name for path in (ROOT / "docs/en/modules").glob("*.md")}
    russian = {path.name for path in (ROOT / "docs/ru/modules").glob("*.md")}

    assert english == russian


def test_there_is_a_document_for_every_module_and_no_orphans():
    documented = {path.stem for path in (ROOT / "docs/en/modules").glob("*.md")}

    assert documented == set(module_names())


def test_the_checker_runs_on_its_own():
    finished = subprocess.run(
        [sys.executable, str(ROOT / "tools/check_docs.py")], capture_output=True, text=True
    )

    assert finished.returncode == 0, finished.stdout


def test_every_relative_link_points_at_something():
    """A link nobody checks is noticed six months later, by a reader."""
    import re

    root = Path(__file__).resolve().parent.parent
    pages = list((root / "docs").rglob("*.md"))
    pages += [root / name for name in ("README.md", "AGENTS.md", "CONTRIBUTING.md")]

    broken = []
    for page in pages:
        for match in re.finditer(r"\]\(([^)\s#]+)(#[^)]*)?\)", page.read_text(encoding="utf-8")):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if not (page.parent / target).exists():
                broken.append(f"{page.relative_to(root)} -> {target}")

    assert broken == []


def test_every_document_offers_the_way_out():
    """A reader who lands mid-documentation can get home, to the index, and across."""
    root = Path(__file__).resolve().parent.parent
    for language, other in (("en", "Русский"), ("ru", "English")):
        for page in (root / "docs" / language).rglob("*.md"):
            if page.name == "README.md":
                continue
            head = page.read_text(encoding="utf-8").splitlines()[2]
            assert head.startswith("[HEID//R]"), page
            assert other in head, page
