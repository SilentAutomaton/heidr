import random

import pytest

from heidr import registry
from heidr.capabilities import Terminal
from heidr.visuals.art import plasma, reveal
from heidr.visuals.canvas import Canvas, Frame
from heidr.visuals.paint import ASCII, BLOCKS, BRAILLE, blank, centre, lines, resample, row, stamp

from tests.test_app import make_app

CONSOLE = Terminal(colours=16, glyphs="blocks", graphics="none")
POOR = Terminal(colours=8, glyphs="ascii", graphics="none")
SIZES = [(20, 5), (40, 8), (80, 12), (120, 20), (200, 40)]


def frame(width=40, height=8, tick=0, ramp=ASCII, payload=None):
    return Frame(width=width, height=height, tick=tick, ramp=ramp, glyphs="braille", payload=payload)


# Brushes


def test_bars_are_fitted_to_the_columns_on_screen():
    assert len(resample([0.0, 1.0] * 32, 20)) == 20
    assert len(resample([0.5] * 3, 9)) == 9
    assert resample([0.1, 0.2, 0.3], 3) == [0.1, 0.2, 0.3]


def test_no_columns_means_no_output():
    assert resample([0.5], 0) == []
    assert resample([], 10) == []


def test_the_ramp_runs_from_empty_to_full():
    assert row([0.0, 1.0], ASCII) == " @"
    assert row([0.0, 1.0], BLOCKS) == " █"
    assert row([0.0, 1.0], BRAILLE) == " ⣿"
    assert row([-5.0, 5.0], ASCII) == " @"


def test_a_stamp_leaves_its_spaces_transparent():
    grid = blank(5, 3)
    grid = stamp(grid, ["ab", " c"], 1, 1)

    assert lines(grid) == ["     ", " ab  ", "  c  "]


def test_a_stamp_is_clipped_at_the_edges():
    grid = stamp(blank(3, 2), ["xxxxx"], 1, 1)

    assert lines(grid) == ["   ", " xx"]


def test_centring_puts_the_art_in_the_middle():
    grid = centre(blank(5, 3), ["ab"])

    assert lines(grid)[1] == " ab  "


# The canvas


@pytest.mark.asyncio
async def test_the_canvas_shows_what_its_painter_paints(default_config):
    async with make_app(default_config).run_test() as pilot:
        canvas = pilot.app.query_one("#visual", Canvas)

        assert canvas.painter is not None
        assert canvas.render() != ""


@pytest.mark.asyncio
async def test_the_canvas_advances_on_its_own(default_config):
    async with make_app(default_config).run_test() as pilot:
        canvas = pilot.app.query_one("#visual", Canvas)
        started = canvas.tick
        canvas.advance()
        canvas.advance()

        assert canvas.tick == started + 2


@pytest.mark.asyncio
async def test_swapping_the_painter_starts_the_count_again(default_config):
    async with make_app(default_config).run_test() as pilot:
        canvas = pilot.app.query_one("#visual", Canvas)
        canvas.advance()
        pilot.app.show_visual("waterfall")

        assert canvas.tick == 0


# Every registered animation


@pytest.mark.parametrize("name", sorted(registry.ANIMATIONS))
@pytest.mark.parametrize("size", SIZES)
def test_an_animation_fits_the_space_it_is_given(name, size):
    width, height = size
    for entry in registry.ANIMATIONS[name]:
        painter = entry.make()
        painter.feed([0.5] * 16 if entry.event == "spectrum" else "a line of text")
        drawn = painter.paint(frame(width, height, tick=3, ramp=painter.ramp))

        assert len(drawn) <= height
        assert all(len(line) <= width for line in drawn)


@pytest.mark.parametrize("name", sorted(registry.ANIMATIONS))
def test_repainting_the_same_frame_changes_nothing(name):
    """A tick is one step. Drawing it twice must not advance anything.

    Textual repaints whenever it likes — on a resize, on a scroll — and an
    animation that stepped on every repaint would run at the speed of the
    terminal rather than its own.
    """
    if name == "reveal":
        return  # noise by design; its own tests cover what is stable

    for entry in registry.ANIMATIONS[name]:
        painter = entry.make()
        painter.feed([0.2, 0.8] * 8)
        shape = frame(40, 6, tick=5, ramp=painter.ramp)

        assert painter.paint(shape) == painter.paint(shape)


def test_an_animation_with_no_data_yet_draws_nothing_rather_than_failing():
    for entries in registry.ANIMATIONS.values():
        for entry in entries:
            if entry.event:
                assert entry.make().paint(frame()) == []


# Plasma


def test_the_plasma_field_fills_the_space_it_is_given():
    rows = plasma.field(width=12, height=3, phase=0.0)

    assert len(rows) == 3 and all(len(line) == 12 for line in rows)
    assert all(0.0 <= value <= 1.0 for line in rows for value in line)


def test_the_plasma_field_moves_with_its_phase():
    assert plasma.field(10, 2, phase=0.0) != plasma.field(10, 2, phase=5.0)
    assert plasma.field(10, 2, phase=0.0) == plasma.field(10, 2, phase=0.0)


def test_the_cog_turns():
    from heidr.visuals.art.cog import Cog
    from heidr.visuals.canvas import Frame

    painter = Cog()
    still = painter.paint(Frame(40, 11, 0, "#", "ascii"))

    assert still != painter.paint(Frame(40, 11, 9, "#", "ascii"))


def test_the_gear_train_fills_the_width_and_meshes():
    from heidr.visuals.art.cog import train

    narrow = train(40, 11)
    wide = train(120, 11)

    assert len(wide) > len(narrow)
    # Neighbours turn against each other, the way real teeth force them to.
    directions = [gear[3] for gear in wide]
    assert all(one != other for one, other in zip(directions, directions[1:]))


def test_the_gears_grow_with_the_pane():
    from heidr.visuals.art.cog import train

    assert train(80, 30)[0][2] > train(80, 10)[0][2]


def test_a_line_reaches_both_ends():
    from heidr.visuals.paint import blank, line, lines

    drawn = lines(line(blank(5, 3), 0, 0, 4, 2, "#"))

    assert drawn[0][0] == "#" and drawn[2][4] == "#"


def test_a_line_outside_the_grid_does_not_fall_over():
    from heidr.visuals.paint import blank, line, lines

    assert lines(line(blank(3, 2), -5, -5, 9, 9, "#"))


# Reveal


def test_unresolved_characters_are_replaced_by_noise():
    shown = reveal.scramble("secret", set(), random.Random(1))

    assert len(shown) == len("secret")
    assert shown != "secret"


def test_spaces_and_line_breaks_never_scramble():
    shown = reveal.scramble("a b\nc", set(), random.Random(1))

    assert shown[1] == " " and shown[3] == "\n"


def test_resolved_positions_show_the_real_character():
    shown = reveal.scramble("secret", {0, 5}, random.Random(1))

    assert shown[0] == "s" and shown[5] == "t"


def test_every_position_resolves_in_the_end():
    resolved: set[int] = set()
    rng = random.Random(2)
    for _ in range(200):
        resolved = reveal.next_resolved(20, resolved, 0.12, rng)

    assert len(resolved) == 20


# Choosing by terminal


def test_the_richest_drawable_variant_is_chosen():
    assert registry.pick_animation("waterfall", "braille").glyphs == "braille"
    assert registry.pick_animation("waterfall", "blocks").glyphs == "blocks"
    assert registry.pick_animation("waterfall", "ascii").glyphs == "ascii"


def test_an_unknown_animation_has_nothing_to_choose():
    assert registry.pick_animation("nothing-like-this", "braille") is None


@pytest.mark.asyncio
async def test_a_console_gets_the_block_waterfall(default_config):
    async with make_app(default_config, terminal=CONSOLE).run_test() as pilot:
        pilot.app.show_visual("waterfall")

        assert pilot.app.query_one("#visual", Canvas).painter.ramp == BLOCKS


@pytest.mark.asyncio
async def test_the_poorest_terminal_still_gets_a_waterfall(default_config):
    async with make_app(default_config, terminal=POOR).run_test() as pilot:
        pilot.app.show_visual("waterfall")

        assert pilot.app.query_one("#visual", Canvas).painter.ramp == ASCII


@pytest.mark.asyncio
async def test_events_reach_the_painter(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.show_visual("waterfall")
        pilot.app.bus.emit("spectrum", [0.2] * 16)

        assert list(pilot.app.query_one("#visual", Canvas).painter.rows) == [[0.2] * 16]


@pytest.mark.asyncio
async def test_swapping_a_painter_unsubscribes_the_old_one(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.show_visual("waterfall")
        first = pilot.app.query_one("#visual", Canvas).painter

        pilot.app.show_visual("plasma")
        pilot.app.bus.emit("spectrum", [1.0] * 4)

        assert list(first.rows) == []


# Life


def test_a_block_is_a_still_life():
    from heidr.visuals.art.life import step

    block = {(1, 1), (1, 2), (2, 1), (2, 2)}

    assert step(block, 8, 8) == block


def test_a_blinker_has_a_period_of_two():
    from heidr.visuals.art.life import step

    vertical = {(2, 1), (2, 2), (2, 3)}
    horizontal = step(vertical, 8, 8)

    assert horizontal == {(1, 2), (2, 2), (3, 2)}
    assert step(horizontal, 8, 8) == vertical


def test_a_lonely_cell_dies():
    from heidr.visuals.art.life import step

    assert step({(3, 3)}, 8, 8) == set()


def test_the_board_is_sown_again_when_it_settles():
    from heidr.visuals.art.life import Life

    painter = Life()
    painter.reseed(20, 8)
    painter.cells = {(1, 1), (1, 2), (2, 1), (2, 2)}
    for tick in range(6):
        painter.paint(frame(20, 8, tick=tick, ramp=painter.ramp))

    assert painter.cells != {(1, 1), (1, 2), (2, 1), (2, 2)}


# Moon


def test_a_full_moon_is_lit_all_over():
    import math

    from heidr.visuals.art.moon import disc

    drawn = "".join(disc(28, 9, math.pi, BLOCKS))

    assert "▂" not in drawn
    assert "█" in drawn


def test_a_new_moon_is_dark_all_over():
    from heidr.visuals.art.moon import disc

    drawn = "".join(disc(28, 9, 0.01, BLOCKS))

    assert "█" not in drawn
    assert "▂" in drawn


def test_the_quarters_light_opposite_halves():
    import math

    from heidr.visuals.art.moon import disc

    first = disc(28, 9, math.pi / 2, BLOCKS)[4]
    last = disc(28, 9, 3 * math.pi / 2, BLOCKS)[4]

    assert first.index("█") > last.index("█")
    assert first.rstrip()[-1] == "█" and last.strip()[0] == "█"


# The animation has to reach the screen, not only the widget


def composited(app) -> list[str]:
    """What the terminal would really receive, layer by layer flattened."""
    return ["".join(segment.text for segment in row) for row in app.screen._compositor.render_strips()]


@pytest.mark.asyncio
@pytest.mark.parametrize("size", [(40, 12), (60, 20), (80, 24), (120, 40), (200, 50)])
async def test_the_animation_is_visible_around_the_panel(default_config, size):
    """A widget above the canvas hides its characters, transparent or not.

    This is the test that was missing when the animations disappeared for a
    whole cycle: the old one checked widget sizes, which were correct all along.
    """
    async with make_app(default_config).run_test(size=size) as pilot:
        # Plasma fills every cell, so absence here means absence everywhere.
        pilot.app.show_visual("plasma")
        await pilot.pause()
        rows = composited(pilot.app)
        ramp = set(pilot.app.query_one("#visual", Canvas).painter.ramp) - {" "}

        assert any(character in ramp for character in rows[0])
        assert any(character in ramp for row in rows for character in row[:2])


@pytest.mark.asyncio
async def test_the_panel_never_covers_the_whole_screen(default_config):
    async with make_app(default_config).run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        body = pilot.app.query_one("#body")

        assert body.region.width < pilot.app.size.width
