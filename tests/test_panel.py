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
