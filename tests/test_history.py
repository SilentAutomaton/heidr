"""What was typed before comes back, and the unfinished line is not lost."""

import pytest

from heidr.history import History
from heidr.ui.commandline import CommandLine

from tests.test_app import make_app


@pytest.fixture
def kept(tmp_path):
    return History(tmp_path / "commands")


def test_the_past_is_walked_back_and_forward(kept):
    kept.add("first")
    kept.add("second")

    assert kept.back("") == "second"
    assert kept.back("") == "first"
    assert kept.forward() == "second"


def test_the_start_of_the_past_is_the_end_of_the_walk(kept):
    kept.add("only")

    assert kept.back("") == "only"
    assert kept.back("") == "only"


def test_the_unfinished_line_comes_back(kept):
    kept.add("first")

    kept.back("half wri")

    assert kept.forward() == "half wri"


def test_a_line_repeated_at_once_is_kept_once(kept):
    kept.add("same")
    kept.add("same")

    assert kept.lines == ["same"]


def test_an_empty_line_is_not_kept(kept):
    kept.add("   ")

    assert kept.lines == []


def test_the_past_outlives_the_program(tmp_path):
    History(tmp_path / "commands").add("remembered")

    assert History(tmp_path / "commands").lines == ["remembered"]


def test_only_the_last_lines_are_kept(tmp_path):
    short = History(tmp_path / "commands", limit=3)
    for number in range(6):
        short.add(str(number))

    assert short.lines == ["3", "4", "5"]


@pytest.mark.asyncio
async def test_the_arrows_bring_back_a_command(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        await pilot.press("colon", "up")

        assert pilot.app.query_one(CommandLine).buffer == "modules"


@pytest.mark.asyncio
async def test_control_p_and_n_do_the_same(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        await pilot.press("colon", "ctrl+p", "ctrl+n")

        assert pilot.app.query_one(CommandLine).buffer == ""


@pytest.mark.asyncio
async def test_questions_and_commands_are_looked_through_apart(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"mute", "enter")
        await pilot.press("i", "up")

        assert pilot.app.query_one(CommandLine).buffer == ""
