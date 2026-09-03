import random

import pytest

from heidr import registry
from heidr.capabilities import Terminal
from heidr.visuals import palette
from heidr.visuals.canvas import Canvas

from tests.test_app import make_app

TRUECOLOR = 16777216
INDEXED = 256
CONSOLE = 16


def rng():
    return random.Random(1)


def test_a_colour_is_exact_where_the_terminal_can_be_exact():
    assert palette.tint("cog", TRUECOLOR, rng()).startswith("#")


def test_a_colour_steps_down_to_an_index_at_256():
    assert palette.tint("cog", INDEXED, rng()).startswith("color(")


def test_a_bare_console_is_left_alone():
    assert palette.tint("cog", CONSOLE, rng()) == ""


def test_the_sign_and_the_answer_keep_the_accent():
    for name in palette.KEEPS_ACCENT:
        assert palette.tint(name, TRUECOLOR, rng()) == ""


def test_an_animation_with_no_entry_is_left_alone():
    assert palette.tint("nothing of the kind", TRUECOLOR, rng()) == ""


def test_the_same_animation_is_not_the_same_colour_twice_running():
    drawn = {palette.tint("cog", TRUECOLOR, random.Random(seed)) for seed in range(20)}

    assert len(drawn) > 1


def test_every_registered_animation_has_a_colour_or_keeps_the_accent():
    for name in registry.ANIMATIONS:
        assert name in palette.TINTS or name in palette.KEEPS_ACCENT


def test_no_colour_is_a_pure_primary():
    """A saturated primary vibrates on a dark ground; the table forbids it."""
    for offered in palette.TINTS.values():
        for exact, _index in offered:
            channels = [int(exact[start : start + 2], 16) for start in (1, 3, 5)]
            assert max(channels) - min(channels) < 200
            assert 50 < sum(channels) / 3 < 220


def tinted(app) -> bool:
    """Whether the animation has a colour of its own rather than the accent."""
    return app.query_one("#visual", Canvas).styles.inline.has_rule("color")


@pytest.mark.asyncio
async def test_the_canvas_is_tinted_when_the_animation_is_swapped(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.show_visual("cog")

        assert tinted(pilot.app)


@pytest.mark.asyncio
async def test_the_answer_takes_the_tint_off_again(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.show_visual("cog")
        pilot.app.show_visual("reveal")

        assert not tinted(pilot.app)


@pytest.mark.asyncio
async def test_a_bare_console_canvas_is_never_tinted(default_config):
    app = make_app(default_config)
    app.terminal = Terminal(colours=16, glyphs="blocks", graphics="none")
    async with app.run_test() as pilot:
        pilot.app.show_visual("cog")

        assert not tinted(pilot.app)
