"""The interface must stay alive while a rite runs.

Every test here corresponds to one of the four causes of a real failure: the
draw ran on the interface thread, events had no listener, the answer pane was
written once at the end, and a module's refusal crashed the program.
"""

import threading

import pytest

from heidr import entropy, registry, session
from heidr.contracts import Cancelled, Key, Material, Unavailable
from heidr.events import Bus
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine

from tests.test_app import make_app

QUESTION = "is the roof the right place"


@pytest.fixture
def offline(monkeypatch):
    monkeypatch.setattr(entropy, "collect", lambda ctx, seconds=2.0, budget_s=6.0: [])


@pytest.fixture
def only(temporary_slot):
    """Register one rite and nothing else, so the draw is predictable."""

    def install(world_run, reading_run=None):
        registry.question("q")(lambda ctx, text: Key(seed=1, anchors=()))
        registry.world("w")(world_run)
        registry.reading("r")(reading_run or (lambda ctx, text, material: iter(())))

    return install


# The bus keeps count of what nobody heard


def test_an_event_with_no_listener_is_counted():
    bus = Bus()
    bus.emit("token", "lost")
    bus.emit("token", "also lost")

    assert bus.dropped == {"token": 2}


def test_a_heard_event_is_not_counted():
    bus = Bus()
    bus.subscribe("token", lambda payload: None)
    bus.emit("token", "heard")

    assert bus.dropped == {}


@pytest.mark.asyncio
async def test_a_whole_draw_drops_nothing(default_config, offline, only):
    only(lambda ctx, key: Material("found", source="fake"),
         lambda ctx, text, material: iter(["one", "two"]))

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()
        while pilot.app.drawing:
            await pilot.pause()

        # Anything emitted during a rite must have had somewhere to go.
        assert pilot.app.bus.dropped == {}


# The interface stays alive


@pytest.mark.asyncio
async def test_the_interface_answers_while_a_draw_runs(default_config, offline, only):
    holding = threading.Event()

    def slow(ctx, key):
        holding.wait(timeout=10)
        return Material("found at last", source="fake")

    only(slow)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()
        assert pilot.app.drawing is True

        # If perform were still on this thread, none of the following could run.
        await pilot.press("colon")
        assert pilot.app.edit_mode == "COMMAND"
        await pilot.press("escape")

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()

        assert "found at last" in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_the_stage_shows_before_the_draw_is_over(default_config, offline, only):
    holding = threading.Event()

    def slow(ctx, key):
        holding.wait(timeout=10)
        return Material("found", source="fake")

    only(slow)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()

        assert pilot.app.query_one(StatusLine).rite in ("q", "w")
        holding.set()
        while pilot.app.drawing:
            await pilot.pause()


@pytest.mark.asyncio
async def test_the_stage_bar_fills_up_as_the_rite_runs(default_config, offline, only):
    holding = threading.Event()

    def slow(ctx, key):
        holding.wait(timeout=10)
        return Material("found", source="fake")

    only(slow)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()
        halfway = str(pilot.app.query_one("#body").content)

        assert "q" in halfway and "..." in halfway

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()

        assert "..." not in str(pilot.app.query_one("#body").content)


# The answer arrives as it is spoken


@pytest.mark.asyncio
async def test_the_reading_appears_line_by_line(default_config, offline, only):
    holding = threading.Event()

    def slowly(ctx, question, material):
        yield "the first line"
        holding.wait(timeout=10)
        yield "the second line"

    only(lambda ctx, key: Material("found", source="fake"), slowly)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        # The first line is written from a worker thread, so waiting for it is
        # part of the test; what matters is that the draw is still running.
        shown = ""
        for _ in range(100):
            await pilot.pause()
            shown = str(pilot.app.query_one("#body").content)
            if "the first line" in shown:
                break

        assert "the first line" in shown
        assert "the second line" not in shown

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()

        assert "the second line" in str(pilot.app.query_one("#body").content)


# A refusal is not a crash


@pytest.mark.asyncio
async def test_a_module_that_refuses_does_not_crash_the_program(default_config, offline, only):
    def refuses(ctx, key):
        raise Unavailable("earthquake.usgs.gov did not answer within 12 seconds.")

    only(refuses)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()
        while pilot.app.drawing:
            await pilot.pause()

        assert "did not answer" in pilot.app.query_one(CommandLine).message
        assert pilot.app.is_running


@pytest.mark.asyncio
async def test_an_unexpected_failure_is_reported_not_raised(default_config, offline, only):
    only(lambda ctx, key: 1 / 0)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()
        while pilot.app.drawing:
            await pilot.pause()

        assert "ZeroDivisionError" in pilot.app.query_one(CommandLine).message
        assert pilot.app.is_running


# Stopping, and not starting twice


@pytest.mark.asyncio
async def test_escape_stops_a_draw_and_frees_the_question(default_config, offline, only):
    holding = threading.Event()

    def slow(ctx, key):
        while not ctx.cancelled():
            if holding.wait(timeout=0.05):
                break
        raise Cancelled

    only(slow)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()

        await pilot.press("escape")
        while pilot.app.drawing:
            await pilot.pause()

        assert pilot.app.ledger.last().get("Status") == "void"
        assert pilot.app.ledger.asked_before(QUESTION) is None


@pytest.mark.asyncio
async def test_a_second_draw_is_refused_while_one_runs(default_config, offline, only):
    holding = threading.Event()
    only(lambda ctx, key: (holding.wait(timeout=10), Material("found", source="fake"))[1])

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()

        await pilot.press("i", *"another question", "enter")
        assert "already running" in pilot.app.query_one(CommandLine).message

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()

        assert len(pilot.app.ledger.entries()) == 1


# The session itself


def test_the_session_stops_between_stages(stub_context, tmp_path, monkeypatch):
    from heidr.ledger import Ledger

    monkeypatch.setattr(entropy, "collect", lambda ctx, seconds=2.0, budget_s=6.0: [])
    stopped = stub_context.__class__(
        config=stub_context.config, emit=stub_context.emit, cancelled=lambda: True
    )

    with pytest.raises(Cancelled):
        session.perform(stopped, Ledger(tmp_path / "ledger"), QUESTION)
