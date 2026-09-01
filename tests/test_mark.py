"""The sign, its one colour, and the slogan that does not sit still."""

import pytest

from heidr.strings import NAME, SLOGANS
from heidr.ui import mark

from tests.test_app import make_app


def test_only_the_slashes_carry_the_colour():
    drawn = mark.wordmark("blocks", 16777216)
    coloured = "".join(drawn.plain[span.start : span.end] for span in drawn.spans)

    assert coloured.strip("\n ") != ""
    assert "█" in coloured
    assert len(coloured) < len(drawn.plain) / 2


def test_the_plain_sign_colours_the_slashes_too():
    drawn = mark.wordmark("ascii", 256)

    assert drawn.plain == NAME
    assert drawn.plain[drawn.spans[0].start : drawn.spans[0].end] == "//"


@pytest.mark.parametrize(
    "colours, expected",
    [(16777216, mark.TRUECOLOR), (256, mark.INDEXED), (16, mark.POOR), (8, mark.POOR)],
)
def test_the_colour_steps_down_with_the_terminal(colours, expected):
    assert mark.accent(colours) == expected


def test_the_garbled_slogan_keeps_the_shape_of_the_words():
    scrambled = mark.garble("Ask the Noise.", 3)

    assert len(scrambled) == len("Ask the Noise.")
    assert [len(word) for word in scrambled.split(" ")] == [3, 3, 6]


def test_the_garbled_slogan_changes_with_the_tick():
    assert mark.garble("Ask the Noise.", 1) != mark.garble("Ask the Noise.", 2)
    assert mark.garble("Ask the Noise.", 1) == mark.garble("Ask the Noise.", 1)


def test_a_poor_terminal_never_garbles(default_config):
    assert mark.can_garble("ascii", default_config) is False
    assert mark.can_garble("box", default_config) is False


def test_a_dumb_terminal_never_garbles(default_config, monkeypatch):
    monkeypatch.setenv("TERM", "dumb")

    assert mark.can_garble("blocks", default_config) is False


def test_motion_can_be_switched_off(default_config, monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")
    default_config.set("ui.motion", False)

    assert mark.can_garble("blocks", default_config) is False


def test_a_good_terminal_may_garble(default_config, monkeypatch):
    monkeypatch.setenv("TERM", "xterm-256color")

    assert mark.can_garble("blocks", default_config) is True


@pytest.mark.asyncio
async def test_the_slogan_is_drawn_from_the_dozen(default_config):
    async with make_app(default_config).run_test() as pilot:
        assert pilot.app.slogan in SLOGANS
        assert len(SLOGANS) >= 12


@pytest.mark.asyncio
async def test_the_garbled_slogan_moves_on_the_menu(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.garbled = True
        pilot.app._render_body()
        first = str(pilot.app.query_one("#body").content)
        pilot.app._breathe()

        assert str(pilot.app.query_one("#body").content) != first
