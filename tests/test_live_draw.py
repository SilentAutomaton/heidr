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
def only(temporary_slot, default_config):
    """Register one rite and nothing else, so the draw is predictable.

    Silence is switched off with it: the lot that decides whether the oracle
    speaks is drawn from the clock, and a test that waits for a reading cannot
    be at the mercy of it.
    """

    def install(world_run, reading_run=None):
        default_config.set("rite.silence_chance", 0.0)
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

        # What broke is a fact about the code; the reader is told what it means.
        said = pilot.app.query_one(CommandLine).message
        assert "Error" not in said
        assert "Nothing was spent" in said
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


# The window says what is happening while it is hidden


@pytest.mark.asyncio
async def test_the_window_title_is_the_name_when_nothing_runs(default_config):
    async with make_app(default_config).run_test() as pilot:
        assert pilot.app._title() == "HEID//R"


@pytest.mark.asyncio
async def test_the_window_title_spins_and_names_the_stage(default_config, offline, only):
    holding = threading.Event()

    def slow(ctx, key):
        ctx.emit("progress", (2, 4))
        holding.wait(timeout=10)
        return Material("found", source="fake")

    only(slow)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        for _ in range(100):
            await pilot.pause()
            if pilot.app.progress is not None:
                break
        title = pilot.app._title()

        assert title.endswith("w 2/4")
        assert title[0] in "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏|/-\\"

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()

        assert pilot.app._title() == "HEID//R"


@pytest.mark.asyncio
async def test_the_title_says_nothing_it_does_not_know(default_config, offline, only):
    holding = threading.Event()
    only(lambda ctx, key: holding.wait(timeout=10) or Material("found", source="fake"))

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()

        # No empty gap where a module name would go.
        assert "—  " not in pilot.app._title()

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()


@pytest.mark.asyncio
async def test_a_stage_that_says_nothing_counts_itself(default_config, offline, only):
    holding = threading.Event()

    def slow(ctx, key):
        holding.wait(timeout=10)
        return Material("found", source="fake")

    only(slow)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        await pilot.pause()

        assert pilot.app._title().endswith("/3")

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()


@pytest.mark.asyncio
async def test_a_chosen_chain_reaches_the_draw(default_config, offline, temporary_slot):
    """What the command pinned is what the rite runs."""
    registry.question("q")(lambda ctx, text: Key(seed=1, anchors=()))
    registry.world("w")(lambda ctx, key: Material("found", source="fake"))
    registry.world("other")(lambda ctx, key: Material("not this one", source="fake"))
    registry.reading("r")(lambda ctx, text, material: iter(["said"]))
    default_config.set("rite.silence_chance", 0.0)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw q//w//r", "enter")
        await pilot.press(*QUESTION, "enter")
        while pilot.app.drawing:
            await pilot.pause()

        shown = str(pilot.app.query_one("#body").content)
        assert "found" in shown and "said" in shown
        assert "not this one" not in shown
        # The pin is spent by the draw, so the next question is drawn as usual.
        assert pilot.app.pinned == ""


@pytest.mark.asyncio
async def test_the_material_shows_before_the_reading_finishes(default_config, offline, only):
    """The reading can take a minute; what was found is on screen at once."""
    holding = threading.Event()

    def slowly(ctx, question, material):
        holding.wait(timeout=10)
        yield "at last"

    only(lambda ctx, key: Material("the found thing", source="fake"), slowly)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *QUESTION, "enter")
        shown = ""
        for _ in range(100):
            await pilot.pause()
            shown = str(pilot.app.query_one("#body").content)
            if "the found thing" in shown:
                break

        assert "the found thing" in shown
        assert "at last" not in shown

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()

        assert "at last" in str(pilot.app.query_one("#body").content)


# What gave way is said out loud


@pytest.mark.asyncio
async def test_a_module_giving_way_is_written_into_the_panel(default_config, offline, temporary_slot):
    registry.question("q")(lambda ctx, text: Key(seed=1, anchors=()))
    registry.world("empty")(lambda ctx, key: (_ for _ in ()).throw(Unavailable("the feed is quiet")))
    registry.world("full")(lambda ctx, key: Material("found at last", source="fake"))
    registry.reading("r")(lambda ctx, text, material: iter(["said"]))
    default_config.set("rite.silence_chance", 0.0)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw q//empty//r", "enter")
        await pilot.press(*QUESTION, "enter")
        while pilot.app.drawing:
            await pilot.pause()

        shown = str(pilot.app.query_one("#body").content)
        assert "empty could not answer" in shown
        assert "found at last" in shown
        # An ordinary outcome, not a fault: no accent, no exclamation.
        assert pilot.app.notice == ""
        assert pilot.app.bus.dropped == {}


@pytest.mark.asyncio
async def test_the_bar_shows_who_is_running_not_who_gave_way(default_config, offline, temporary_slot):
    holding = threading.Event()
    registry.question("q")(lambda ctx, text: Key(seed=1, anchors=()))
    registry.world("empty")(lambda ctx, key: (_ for _ in ()).throw(Unavailable("quiet")))

    def slow(ctx, key):
        holding.wait(timeout=10)
        return Material("found", source="fake")

    registry.world("full")(slow)
    registry.reading("r")(lambda ctx, text, material: iter(["said"]))
    default_config.set("rite.silence_chance", 0.0)

    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"draw q//empty//r", "enter")
        await pilot.press(*QUESTION, "enter")
        for _ in range(100):
            await pilot.pause()
            if "full" in pilot.app.stages:
                break

        assert pilot.app.stages == ["q", "full"]
        assert pilot.app._title().endswith("full 2/3")

        holding.set()
        while pilot.app.drawing:
            await pilot.pause()
