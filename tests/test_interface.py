"""What the interface does, not what it draws.

Behaviour and layout decisions are tested here; rendered pixels are not. A
screenshot test breaks on every unrelated change and teaches nothing.
"""

import pytest

from heidr import entropy
from heidr.capabilities import Terminal
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine

from tests.test_app import make_app

SIZES = [(40, 12), (60, 20), (80, 24), (120, 40), (200, 50)]
CONSOLE = Terminal(colours=16, glyphs="blocks", graphics="none")


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(entropy, "collect", lambda ctx, seconds=2.0, budget_s=6.0: [])


# Modes


@pytest.mark.asyncio
async def test_the_three_modes_are_reachable_and_reversible(default_config):
    async with make_app(default_config).run_test() as pilot:
        assert pilot.app.edit_mode == "NORMAL"

        await pilot.press("i")
        assert pilot.app.edit_mode == "INSERT"
        await pilot.press("escape")
        assert pilot.app.edit_mode == "NORMAL"

        await pilot.press("colon")
        assert pilot.app.edit_mode == "COMMAND"
        await pilot.press("escape")
        assert pilot.app.edit_mode == "NORMAL"


@pytest.mark.asyncio
async def test_typing_in_normal_mode_does_not_reach_the_line(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("z", "x", "c")

        assert pilot.app.query_one(CommandLine).buffer == ""


@pytest.mark.asyncio
async def test_backspace_removes_what_was_typed(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"help", "backspace", "backspace")

        assert pilot.app.query_one(CommandLine).buffer == "he"


# Commands


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "command, view",
    [("modules", "modules"), ("settings", "settings"), ("ledger", "ledger")],
)
async def test_each_browser_command_opens_its_view(default_config, command, view):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *command, "enter")

        assert pilot.app.view == view


@pytest.mark.asyncio
async def test_ask_and_draw_both_start_a_question(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw", "enter")
        assert pilot.app.edit_mode == "INSERT"

        await pilot.press("escape")
        await pilot.press("colon", *"ask", "enter")
        assert pilot.app.edit_mode == "INSERT"


@pytest.mark.asyncio
async def test_an_empty_ledger_says_what_to_do(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"ledger", "enter")

        assert "No draws yet" in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_a_past_draw_can_be_read_again(default_config, offline):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *"what now", "enter")
        await pilot.pause()

        await pilot.press("colon", *"ledger", "enter")
        assert len(pilot.app.rows) == 1

        await pilot.press("enter")
        assert pilot.app.view == "rite"
        assert "what now" in str(pilot.app.query_one("#body").content)


# Keymap


@pytest.mark.asyncio
async def test_the_leader_needs_a_second_key(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space")
        assert pilot.app.leader_pending is True
        assert pilot.app.edit_mode == "NORMAL"

        await pilot.press("h")
        assert pilot.app.leader_pending is False


@pytest.mark.asyncio
async def test_an_unbound_leader_key_does_nothing(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space", "z")

        assert pilot.app.edit_mode == "NORMAL"


@pytest.mark.asyncio
async def test_a_rebound_key_replaces_the_default(default_config, tmp_path):
    (tmp_path / "keymap.toml").write_text('[normal]\n"q" = "quit"\n"i" = "modules"\n')
    async with make_app(default_config, user_dir=tmp_path).run_test() as pilot:
        await pilot.press("i")

        assert pilot.app.view == "modules"
        assert pilot.app.edit_mode == "NORMAL"


# Size


@pytest.mark.asyncio
@pytest.mark.parametrize("size", SIZES)
async def test_the_interface_survives_every_size(default_config, size):
    async with make_app(default_config).run_test(size=size) as pilot:
        await pilot.press("colon", *"modules", "enter")

        assert pilot.app.query_one("#body") is not None
        assert pilot.app.query_one(StatusLine) is not None


@pytest.mark.asyncio
async def test_resizing_between_the_extremes_keeps_the_view(default_config):
    async with make_app(default_config).run_test(size=(200, 50)) as pilot:
        await pilot.press("colon", *"settings", "enter")
        rows = len(pilot.app.rows)

        await pilot.resize_terminal(40, 12)
        await pilot.pause()

        assert pilot.app.view == "settings"
        assert len(pilot.app.rows) == rows


@pytest.mark.asyncio
async def test_a_terminal_too_small_says_so_and_recovers(default_config):
    async with make_app(default_config).run_test(size=(80, 24)) as pilot:
        await pilot.resize_terminal(30, 8)
        await pilot.pause()
        assert "Terminal too small" in str(pilot.app.query_one("#body").content)

        await pilot.resize_terminal(80, 24)
        await pilot.pause()
        assert "Terminal too small" not in str(pilot.app.query_one("#body").content)


def test_the_status_line_sheds_fields_from_the_right():
    line = StatusLine()
    line.mode = "NORMAL"
    line.rite = "planetary//hline//iching"
    line.provider = "ollama"

    wide = line._fit(120)
    narrow = line._fit(38)

    assert "ollama" in wide and "planetary" in wide
    assert "ollama" not in narrow
    assert narrow.startswith("NORMAL")


# Terminal capability


@pytest.mark.asyncio
async def test_a_console_gets_the_plain_stylesheet_and_still_works(default_config):
    async with make_app(default_config, terminal=CONSOLE).run_test() as pilot:
        await pilot.press("colon", *"checkhealth", "enter")

        assert pilot.app.css_path[0].name == "theme_tty.tcss"
        assert "terminal" in str(pilot.app.query_one("#body").content)
