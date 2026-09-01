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
