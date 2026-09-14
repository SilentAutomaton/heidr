"""The installer scripts and the flag they configure the program with."""

import subprocess
from pathlib import Path

import pytest

from heidr import config, health
from heidr.__main__ import as_value, main

ROOT = Path(__file__).resolve().parent.parent
SHELL = ROOT / "install.sh"
POWERSHELL = ROOT / "install.ps1"


# Settings from the command line


def written(path: Path) -> dict:
    return config.read(path / "heidr" / "config.toml")


def test_a_setting_written_from_the_shell_keeps_its_type(tmp_path, monkeypatch):
    """A thread count stored as "4" is read back as a string and breaks the run."""
    monkeypatch.setattr(config, "USER_DIR", tmp_path / "heidr")

    assert main(["--set", "stt.threads=4", "--set", "llm.think=true"]) == 0

    saved = written(tmp_path)
    assert saved["stt"]["threads"] == 4
    assert saved["llm"]["think"] is True


def test_a_name_the_configuration_does_not_hold_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DIR", tmp_path / "heidr")

    assert main(["--set", "nonsense.key=1"]) == 1
    assert "nonsense" not in written(tmp_path)


def test_nothing_is_written_until_every_pair_is_understood(tmp_path, monkeypatch):
    """Half a configuration is harder to undo than none."""
    monkeypatch.setattr(config, "USER_DIR", tmp_path / "heidr")

    assert main(["--set", "stt.threads=4", "--set", "no-equals-sign"]) == 1
    # The example configuration is copied before any flag is read, so what
    # proves nothing was written is the value, not the file.
    assert written(tmp_path).get("stt", {}).get("threads") == 0


def test_a_module_setting_is_accepted_though_the_defaults_never_hold_it(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "USER_DIR", tmp_path / "heidr")

    assert main(["--set", "modules.fm_voice.stops=7"]) == 0
    assert written(tmp_path)["modules"]["fm_voice"]["stops"] == 7


@pytest.mark.parametrize(
    "written_value, wanted",
    [("true", True), ("FALSE", False), ("4", 4), ("0.5", 0.5), ("whisper_cpp", "whisper_cpp")],
)
def test_a_value_is_read_as_what_it_looks_like(written_value, wanted):
    assert as_value(written_value) == wanted


# The scripts


def test_the_shell_installer_parses():
    subprocess.run(["sh", "-n", str(SHELL)], check=True)


def test_both_installers_name_this_repository():
    """A typo in the slug is the failure that would make an installer useless."""
    remote = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    slug = remote.removesuffix(".git").split("github.com")[-1].lstrip(":/")

    for script in (SHELL, POWERSHELL):
        assert slug in script.read_text(encoding="utf-8"), script


def test_the_installers_offer_what_the_program_looks_for():
    """The scripts and the health report must not drift apart."""
    both = SHELL.read_text(encoding="utf-8") + POWERSHELL.read_text(encoding="utf-8")
    for tool in ("rtl-sdr",) + health.STREAM_TOOLS:
        assert tool in both, tool


def test_the_installers_do_not_ask_the_latest_release_for_a_nightly_binary():
    """whisper.cpp and llama.cpp publish nothing on the release marked latest."""
    for script in (SHELL, POWERSHELL):
        text = script.read_text(encoding="utf-8")
        assert "releases?per_page=" in text, script
        assert "releases/latest" not in text, script
