"""What the panel does to text before the reader sees it."""

import pytest

from heidr.ui import panel

from tests.test_app import make_app

LONG = "x" * 300


def test_a_long_line_is_folded_rather_than_cut():
    folded = panel.wrap(LONG, 40)

    assert len(folded) == 8
    assert "".join(folded) == LONG


def test_the_line_breaks_already_there_are_kept():
    assert panel.wrap("one\ntwo", 40) == ["one", "two"]


def test_a_long_run_without_spaces_still_breaks():
    """Base64 and mojibake have no spaces to break on, and must break anyway."""
    folded = panel.wrap("abcdefghij" * 5, 10)

    assert all(len(line) <= 10 for line in folded)


def test_too_much_material_is_shortened_and_says_by_how_much():
    shown = panel.shorten("word " * 400, 40, lines=4)

    assert len(shown) == 5
    assert "more characters" in shown[-1]


def test_material_that_fits_is_left_alone():
    assert panel.shorten("short enough", 40, lines=4) == ["short enough"]


def test_the_panel_width_never_grows_past_the_widest():
    assert panel.room(400) == panel.WIDEST
    assert panel.room(50) == 46


@pytest.mark.asyncio
async def test_the_rite_panel_labels_what_it_shows(default_config):
    async with make_app(default_config).run_test(size=(80, 24)) as pilot:
        pilot.app._enter("rite")
        pilot.app.asked = "will it rain"
        pilot.app.found = ("a page of the library", "babel/1f3a")
        pilot.app.said = ["the rain has already fallen"]
        pilot.app.stages = ["gematria", "babel", "iching"]
        pilot.app._render_body()
        shown = str(pilot.app.query_one("#body").content)

        assert "question" in shown and "will it rain" in shown
        assert "found · babel/1f3a" in shown
        assert "answer · iching" in shown


@pytest.mark.asyncio
async def test_the_answer_keeps_its_own_lines(default_config):
    async with make_app(default_config).run_test(size=(80, 24)) as pilot:
        pilot.app._enter("rite")
        pilot.app.asked = "what now"
        pilot.app.said = ["first line", "second line"]
        pilot.app._render_body()
        shown = str(pilot.app.query_one("#body").content)

        assert "  first line\n  second line" in shown


@pytest.mark.asyncio
async def test_a_long_material_line_is_not_lost_on_screen(default_config):
    async with make_app(default_config).run_test(size=(80, 30)) as pilot:
        pilot.app._enter("rite")
        pilot.app.asked = "what now"
        pilot.app.found = (LONG, "fake")
        pilot.app._render_body()
        shown = str(pilot.app.query_one("#body").content)

        # Every character survives the fold; only the line breaks are new.
        assert shown.count("x") == len(LONG)


# A message the reader cannot miss


@pytest.mark.asyncio
async def test_a_refusal_shows_in_the_panel_and_at_the_bottom(default_config):
    from heidr.ui.commandline import CommandLine

    async with make_app(default_config).run_test(size=(80, 24)) as pilot:
        pilot.app._enter("rite")
        pilot.app.asked = "will it rain"
        pilot.app._announce("quake could not reach the feed.")
        shown = str(pilot.app.query_one("#body").content)

        assert "quake could not reach the feed." in shown
        assert shown.startswith("!") or "!  quake" in shown
        assert pilot.app.query_one(CommandLine).level == "error"


@pytest.mark.asyncio
async def test_an_error_line_carries_a_marker_and_the_accent(default_config):
    from heidr.ui.commandline import CommandLine

    async with make_app(default_config).run_test() as pilot:
        line = pilot.app.query_one(CommandLine)
        line.say("nothing to worry about")
        quiet = line.render()
        line.say("the draw stopped", level="error")
        loud = line.render()

        assert quiet.style == ""
        assert str(loud).startswith("!")
        assert loud.style == pilot.app.query_one(CommandLine).accent


@pytest.mark.asyncio
async def test_a_small_message_stays_at_the_bottom(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("right")

        assert pilot.app.notice == ""


# When there is no answer, the panel says why


async def rite_with(pilot, **state):
    pilot.app._enter("rite")
    pilot.app.asked = "will it rain"
    for name, value in state.items():
        setattr(pilot.app, name, value)
    pilot.app._render_body()
    return str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_a_silence_that_was_drawn_says_so(default_config):
    from heidr.strings import text

    async with make_app(default_config).run_test(size=(80, 30)) as pilot:
        pilot.app._enter("rite")
        pilot.app.asked = "will it rain"
        pilot.app._silence(text("answer.silence_drawn"))
        shown = str(pilot.app.query_one("#body").content)

        assert "answer · silence" in shown
        assert "one of them" in shown
        assert "question is spent" in shown


@pytest.mark.asyncio
async def test_a_rite_that_found_nothing_says_the_question_is_free(default_config):
    from heidr.strings import text

    async with make_app(default_config).run_test(size=(80, 30)) as pilot:
        pilot.app._enter("rite")
        pilot.app.asked = "will it rain"
        pilot.app._draw_over(text("note.nothing"), text("answer.nothing", reason="No network."))
        shown = str(pilot.app.query_one("#body").content)

        assert "answer · nothing found" in shown
        assert "Nothing was spent" in shown
        assert "No network." in shown
        # The explanation is the answer now, so there is no shout above it.
        assert pilot.app.notice == ""


@pytest.mark.asyncio
async def test_a_real_answer_still_wins_over_the_explanation(default_config):
    async with make_app(default_config).run_test(size=(80, 30)) as pilot:
        shown = await rite_with(pilot, said=["the rain has fallen"], unanswered=("silence", "no"))

        assert "the rain has fallen" in shown
        assert "answer · silence" not in shown
