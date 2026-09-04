import random
import re

import pytest

from heidr import registry
from heidr.capabilities import Terminal
from heidr.visuals import canvas, palette
from heidr.visuals.canvas import Canvas
from heidr.visuals.paint import ASCII

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


# The gradient


def test_only_the_measured_animations_have_a_gradient():
    assert set(palette.GRADIENTS) == {"waterfall", "scope", "seismo"}
    for name in palette.GRADIENTS:
        assert palette.gradient(name, TRUECOLOR, 8)
    assert palette.gradient("cog", TRUECOLOR, 8) == ()


def test_a_gradient_runs_from_the_first_stop_to_the_last():
    shades = palette.gradient("waterfall", TRUECOLOR, 8)

    assert len(shades) == 8
    assert shades[0] == palette.GRADIENTS["waterfall"][0][0]
    assert shades[-1] == palette.GRADIENTS["waterfall"][-1][0]


def test_a_gradient_steps_down_to_indices_that_cannot_be_mixed():
    shades = palette.gradient("waterfall", INDEXED, 8)

    assert all(shade.startswith("color(") for shade in shades)
    assert set(shades) == {f"color({index})" for _hex, index in palette.GRADIENTS["waterfall"]}


def test_a_bare_console_has_no_gradient_either():
    assert palette.gradient("waterfall", CONSOLE, 8) == ()


def test_a_row_becomes_runs_rather_than_cells():
    shades = ("#000000", "#444444", "#888888", "#ffffff")

    text = canvas.shaded(["  ..==##"], ASCII, shades)

    assert text.plain == "  ..==##"
    assert len(text.spans) == 3
    assert text.spans[0].style == shades[0]
    assert text.spans[-1].style == shades[2]


def test_a_glyph_outside_the_ramp_is_drawn_at_full_strength():
    shades = ("#000000", "#ffffff")

    assert canvas.shaded(["A"], ASCII, shades).spans[0].style == shades[-1]


def test_an_animation_with_no_gradient_still_returns_plain_text():
    painter = registry.pick_animation("cog", "ascii").make()
    board = canvas.Canvas("ascii")
    board.painter = painter

    assert board.tint == ()


# The recorder


@pytest.mark.asyncio
async def test_the_same_frame_is_recorded_the_same_way_twice(default_config):
    """The one property the demo recordings rest on.

    Frames are exported rather than screen-recorded, so a loop closes by
    choosing a frame count instead of by trimming footage. That only holds if
    two runs of the same tick produce the same bytes.
    """
    async def shot(name: str, tick: int) -> str:
        app = make_app(default_config)
        async with app.run_test(size=(60, 16)) as pilot:
            app.query_one("#body").display = False
            random.seed(7)
            app.show_visual(name)
            board = app.query_one("#visual", Canvas)
            board.timer.stop()
            board.timer = None
            if hasattr(board.painter, "rng"):
                board.painter.rng = random.Random(7)
            board.tick = tick
            board.refresh()
            await pilot.pause()
            # The export names its own CSS classes after a number it makes up
            # each time. That reaches the class names and nothing that is drawn,
            # so it is taken out before the two are compared.
            return re.sub(r"terminal-\d+", "terminal", app.export_screenshot(title="HEID//R"))

    for name in ("plasma", "rings", "hexlib"):
        assert await shot(name, 9) == await shot(name, 9)


# The spinner on screen


@pytest.mark.asyncio
async def test_the_spinner_turns_on_screen_while_a_draw_runs(default_config):
    """The window title is not visible when you are looking at the terminal."""
    async with make_app(default_config).run_test() as pilot:
        app = pilot.app
        line = app.query_one("StatusLine")

        app._show_spinner()
        assert line.spinner == ""

        app.drawing = True
        seen = set()
        for _ in range(6):
            app._show_title()
            seen.add(line.spinner)
        assert len(seen) > 1 and "" not in seen

        app.drawing = False
        app._show_spinner()
        assert line.spinner == ""


@pytest.mark.asyncio
async def test_a_silent_step_names_itself_and_turns_the_gears(default_config):
    async with make_app(default_config).run_test() as pilot:
        app = pilot.app
        app.show_visual("waterfall")

        app._working("listening back to 45s")

        assert app.query_one("StatusLine").rite == "listening back to 45s"
        assert tinted(app)
