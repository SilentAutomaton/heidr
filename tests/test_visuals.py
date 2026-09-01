import random

import pytest

from heidr import registry
from heidr.app import HeidrApp
from heidr.capabilities import Terminal
from heidr.visuals import idle, reveal
from heidr.visuals.base import ASCII, BLOCKS, BRAILLE, resample, row
from heidr.visuals.waterfall import Waterfall

from tests.test_app import make_app

CONSOLE = Terminal(colours=16, glyphs="blocks", graphics="none")
POOR = Terminal(colours=8, glyphs="ascii", graphics="none")


# Fitting bars to columns


def test_bars_are_fitted_to_the_columns_on_screen():
    assert len(resample([0.0, 1.0] * 32, 20)) == 20
    assert len(resample([0.5] * 3, 9)) == 9


def test_a_matching_width_is_left_alone():
    bars = [0.1, 0.2, 0.3]
    assert resample(bars, 3) == bars


def test_no_columns_means_no_output():
    assert resample([0.5], 0) == []
    assert resample([], 10) == []


def test_the_ramp_runs_from_empty_to_full():
    assert row([0.0, 1.0], ASCII) == " @"
    assert row([0.0, 1.0], BLOCKS) == " █"
    assert row([0.0, 1.0], BRAILLE) == " ⣿"


def test_values_outside_the_range_are_clamped():
    assert row([-5.0, 5.0], ASCII) == " @"


# Waterfall


def test_the_waterfall_keeps_the_newest_rows_at_the_top():
    fall = Waterfall()
    fall.feed([0.0] * 8)
    fall.feed([1.0] * 8)

    assert list(fall.rows)[-1] == [1.0] * 8


def test_the_waterfall_forgets_old_rows():
    fall = Waterfall()
    for index in range(200):
        fall.feed([index / 200] * 4)

    assert len(fall.rows) == 64


# Idle animation


def test_the_idle_field_fills_the_space_it_is_given():
    rows = idle.field(width=12, height=3, phase=0.0, seed=1)

    assert len(rows) == 3 and all(len(line) == 12 for line in rows)
    assert all(0.0 <= value <= 1.0 for line in rows for value in line)


def test_the_idle_field_drifts_with_its_phase():
    first = idle.field(10, 2, phase=0.0, seed=1)
    later = idle.field(10, 2, phase=1.0, seed=1)

    assert first != later


def test_the_same_seed_draws_the_same_field():
    assert idle.field(10, 2, 0.0, seed=4) == idle.field(10, 2, 0.0, seed=4)


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


def test_the_richest_drawable_waterfall_is_chosen():
    assert registry.pick_visual("waterfall", "braille").glyphs == "braille"
    assert registry.pick_visual("waterfall", "blocks").glyphs == "blocks"
    assert registry.pick_visual("waterfall", "ascii").glyphs == "ascii"


def test_an_unknown_visual_has_nothing_to_choose():
    assert registry.pick_visual("nothing-like-this", "braille") is None


@pytest.mark.asyncio
async def test_a_console_gets_the_block_waterfall(default_config):
    async with make_app(default_config, terminal=CONSOLE).run_test() as pilot:
        pilot.app.show_visual("waterfall")
        mounted = pilot.app.query_one("#visual").children[0]

        assert mounted.ramp == BLOCKS


@pytest.mark.asyncio
async def test_the_poorest_terminal_still_gets_a_waterfall(default_config):
    async with make_app(default_config, terminal=POOR).run_test() as pilot:
        pilot.app.show_visual("waterfall")
        mounted = pilot.app.query_one("#visual").children[0]

        assert mounted.ramp == ASCII


@pytest.mark.asyncio
async def test_events_reach_the_mounted_visual(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.show_visual("waterfall")
        await pilot.pause()

        pilot.app.bus.emit("spectrum", [0.2] * 16)
        mounted = pilot.app.query_one("#visual").children[0]

        assert list(mounted.rows) == [[0.2] * 16]


@pytest.mark.asyncio
async def test_swapping_a_visual_unsubscribes_the_old_one(default_config):
    async with make_app(default_config).run_test() as pilot:
        pilot.app.show_visual("waterfall")
        await pilot.pause()
        first = pilot.app.query_one("#visual").children[0]

        pilot.app.show_visual("idle")
        await pilot.pause()

        pilot.app.bus.emit("spectrum", [1.0] * 4)

        assert list(first.rows) == []
