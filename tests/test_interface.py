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


# The menu


@pytest.mark.asyncio
async def test_the_program_opens_in_the_menu(default_config):
    async with make_app(default_config).run_test() as pilot:
        assert pilot.app.view == "menu"
        assert "ask a question" in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_the_menu_shows_the_command_and_the_key_for_each_entry(default_config):
    async with make_app(default_config).run_test() as pilot:
        shown = str(pilot.app.query_one("#body").content)

        assert ":checkhealth" in shown and "<space>h" in shown


@pytest.mark.asyncio
async def test_a_menu_entry_runs_its_action(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("j", "j", "j", "enter")

        assert pilot.app.view == "modules"


@pytest.mark.asyncio
async def test_the_menu_keeps_its_place_while_you_are_away(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("j", "j", "j", "enter")
        await pilot.press("escape")

        assert pilot.app.view == "menu" and pilot.app.cursor == 3


@pytest.mark.asyncio
async def test_the_wordmark_can_be_switched_off(default_config):
    default_config.set("ui.splash", False)
    async with make_app(default_config).run_test() as pilot:
        shown = str(pilot.app.query_one("#body").content)

        assert "ask a question" in shown and "Ask the Noise" not in shown


# The question field


@pytest.mark.asyncio
async def test_the_question_is_typed_into_the_panel(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *"ok")
        shown = str(pilot.app.query_one("#body").content)

        assert pilot.app.view == "ask"
        assert "ok_" in shown and "Enter asks." in shown


@pytest.mark.asyncio
async def test_the_bottom_line_does_not_repeat_the_question(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *"ok")

        assert str(pilot.app.query_one(CommandLine).render()) == ""


@pytest.mark.asyncio
async def test_the_seeress_moves_while_the_question_is_typed(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i")
        first = str(pilot.app.query_one("#body").content)
        for _ in range(4):
            pilot.app._breathe()

        assert str(pilot.app.query_one("#body").content) != first


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
        assert pilot.app.view == "text"
        assert "what now" in str(pilot.app.query_one("#body").content)


# Keymap


@pytest.mark.asyncio
async def test_the_leader_needs_a_second_key(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space")
        assert pilot.app.pending == "leader"
        assert pilot.app.edit_mode == "NORMAL"

        await pilot.press("h")
        assert pilot.app.pending == ""


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


@pytest.mark.asyncio
async def test_escape_climbs_back_out_of_a_view(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        await pilot.press("escape")

        assert pilot.app.view == "menu"


@pytest.mark.asyncio
async def test_escape_at_the_root_stays_there(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("escape")
        await pilot.press("escape")

        assert pilot.app.views == ["menu"]


@pytest.mark.asyncio
async def test_a_view_entered_twice_is_not_stacked_twice(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        await pilot.press("colon", *"modules", "enter")

        assert pilot.app.views == ["menu", "modules"]


@pytest.mark.asyncio
async def test_the_status_line_says_where_you_are(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")

        assert "modules" in pilot.app.query_one(StatusLine).path


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


# What survives a resize


@pytest.mark.asyncio
async def test_a_question_and_its_answer_survive_a_resize(default_config, offline):
    async with make_app(default_config).run_test(size=(96, 28)) as pilot:
        await pilot.press("i", *"what now", "enter")
        await pilot.pause()
        while pilot.app.drawing:
            await pilot.pause()
        before = str(pilot.app.query_one("#body").content)

        await pilot.resize_terminal(70, 20)
        await pilot.pause()

        assert "what now" in str(pilot.app.query_one("#body").content)
        assert "HEID" not in str(pilot.app.query_one("#body").content)
        assert before.splitlines()[0] in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_shrinking_and_growing_back_restores_the_answer(default_config, offline):
    async with make_app(default_config).run_test(size=(96, 28)) as pilot:
        await pilot.press("i", *"what now", "enter")
        await pilot.pause()
        while pilot.app.drawing:
            await pilot.pause()

        await pilot.resize_terminal(30, 8)
        await pilot.pause()
        assert "Terminal too small" in str(pilot.app.query_one("#body").content)

        await pilot.resize_terminal(96, 28)
        await pilot.pause()
        assert "what now" in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_a_browser_survives_a_resize_and_rewindows(default_config):
    async with make_app(default_config).run_test(size=(96, 40)) as pilot:
        await pilot.press("colon", *"modules", "enter")
        tall = str(pilot.app.query_one("#body").content)

        await pilot.resize_terminal(96, 20)
        await pilot.pause()
        short = str(pilot.app.query_one("#body").content)

        assert pilot.app.view == "modules"
        # The window shrinks with the terminal, and the footer says how far it
        # now reaches.
        assert tall.splitlines()[-1] != short.splitlines()[-1]
        assert short.splitlines()[-1].strip().endswith("of 30")


@pytest.mark.asyncio
async def test_the_health_report_survives_a_resize(default_config):
    async with make_app(default_config).run_test(size=(96, 28)) as pilot:
        await pilot.press("colon", *"checkhealth", "enter")
        await pilot.resize_terminal(80, 24)
        await pilot.pause()

        assert "terminal" in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_the_splash_keeps_its_slogan_across_resizes(default_config):
    async with make_app(default_config).run_test(size=(96, 28)) as pilot:
        first = str(pilot.app.query_one("#body").content)

        await pilot.resize_terminal(80, 24)
        await pilot.pause()

        assert str(pilot.app.query_one("#body").content) == first


def test_the_stylesheets_agree_with_the_layout_arithmetic():
    """A long list is cut to fit, so the padding it is cut by must match."""
    from pathlib import Path

    from heidr.app import PANEL_PADDING

    for name in ("theme_full.tcss", "theme_tty.tcss"):
        style = (Path(__file__).parent.parent / "heidr/ui" / name).read_text()
        panel = style.split("#body")[1]
        top, sides = panel.split("padding: ")[1].split("\n")[0].strip(";").split()
        assert int(top) * 2 == PANEL_PADDING and sides


def test_the_animation_lies_behind_the_panel():
    """The painter gets the whole terminal; the text keeps its own ground."""
    from pathlib import Path

    for name in ("theme_full.tcss", "theme_tty.tcss"):
        style = (Path(__file__).parent.parent / "heidr/ui" / name).read_text()
        assert "layers: back front;" in style
        assert "layer: back;" in style.split("#visual")[1].split("}")[0]


# A rite chosen instead of drawn


@pytest.mark.asyncio
async def test_draw_with_a_chain_pins_it_and_asks(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw blind//babel//iching", "enter")

        assert pilot.app.pinned == "blind//babel//iching"
        assert pilot.app.view == "ask"
        assert pilot.app.edit_mode == "INSERT"


@pytest.mark.asyncio
async def test_draw_without_a_chain_pins_nothing(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw", "enter")

        assert pilot.app.pinned == ""
        assert pilot.app.view == "ask"


@pytest.mark.asyncio
async def test_the_pinned_chain_shows_in_the_status_line(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw blind//babel//iching", "enter")

        assert pilot.app.query_one(StatusLine).rite == "blind//babel//iching"


@pytest.mark.asyncio
async def test_the_menu_can_choose_a_rite_slot_by_slot(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space", "c")
        assert pilot.app.view == "choose.question"

        for slot in ("blind", "babel", "iching"):
            await go_to_row(pilot, slot)
            await pilot.press("enter")

        assert pilot.app.pinned == "blind//babel//iching"
        assert pilot.app.view == "ask"


@pytest.mark.asyncio
async def test_choosing_can_leave_a_slot_to_the_lottery(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space", "c")
        await pilot.press("enter")
        await go_to_row(pilot, "babel")
        await pilot.press("enter")
        await pilot.press("enter")

        assert pilot.app.pinned == "*//babel//*"


@pytest.mark.asyncio
async def test_escape_steps_back_through_the_slots(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space", "c")
        await pilot.press("enter")
        assert pilot.app.view == "choose.world"

        await pilot.press("escape")
        assert pilot.app.view == "choose.question"

        await pilot.press("escape")
        assert pilot.app.view == "menu"


async def go_to_row(pilot, key):
    while pilot.app.rows[pilot.app.cursor][0] != key:
        await pilot.press("down")


@pytest.mark.asyncio
async def test_the_slot_list_says_which_slot_it_is(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space", "c")
        shown = str(pilot.app.query_one("#body").content)

        assert "Which question?" in shown
        assert "leave it to the lottery" in shown
