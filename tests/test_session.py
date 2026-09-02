import pytest

from datetime import datetime, timedelta, timezone

from heidr import entropy, session
from heidr.ledger import Ledger, seal

QUESTION = "should the antenna go on the roof"


@pytest.fixture
def offline(stub_context, monkeypatch):
    monkeypatch.setattr(entropy, "collect", lambda ctx, seconds=2.0: [])
    return stub_context


@pytest.fixture
def ledger(tmp_path):
    return Ledger(tmp_path / "ledger")


def test_a_draw_produces_material_and_records_it(offline, ledger):
    drawn = session.perform(offline, ledger, QUESTION)

    assert drawn.material.source
    assert ledger.last().get("Status") == "complete"
    assert ledger.last().get("Rite") == str(drawn.rite)
    assert ledger.chain_ok()


def test_the_same_question_cannot_be_asked_twice(offline, ledger):
    session.perform(offline, ledger, QUESTION)

    with pytest.raises(session.AlreadyAsked) as refused:
        session.perform(offline, ledger, QUESTION)

    assert refused.value.entry.identifier == "00001"


def test_a_draw_that_found_nothing_releases_the_question(offline, ledger, monkeypatch):
    monkeypatch.setattr(session.rite, "draw", lambda *a, **k: 1 / 0)

    with pytest.raises(ZeroDivisionError):
        session.perform(offline, ledger, QUESTION)

    # An unreachable source must not spend a question. The rule is about not
    # re-rolling an unwelcome answer, and there was no answer.
    assert ledger.last().get("Status") == "void"
    assert ledger.asked_before(QUESTION) is None


def test_after_a_release_the_question_can_be_asked_again(offline, ledger, monkeypatch):
    monkeypatch.setattr(session.rite, "draw", lambda *a, **k: 1 / 0)
    with pytest.raises(ZeroDivisionError):
        session.perform(offline, ledger, QUESTION)

    monkeypatch.undo()
    drawn = session.perform(offline, ledger, QUESTION)

    assert drawn.entry.identifier == "00002"
    assert ledger.chain_ok()


def test_a_rite_with_no_reading_left_frees_the_question(offline, ledger, monkeypatch):
    """Material was found and nobody read it, so the question was not answered."""
    monkeypatch.setattr(session, "_read", _falls_over)

    with pytest.raises(RuntimeError):
        session.perform(offline, ledger, QUESTION)

    assert ledger.last().get("Status") == "broken"
    assert ledger.asked_before(QUESTION) is None


def _falls_over(*args, **kwargs):
    raise RuntimeError("the reading fell over")


def test_a_silent_rite_keeps_the_material_and_says_nothing(offline, ledger):
    offline.config.set("rite.silence_chance", 1.0)

    drawn = session.perform(offline, ledger, QUESTION)

    assert drawn.rite.silent is True
    assert drawn.lines == []
    assert drawn.material.text or drawn.material.source


def test_the_walk_announces_every_stage(offline, ledger, events):
    offline.config.set("rite.silence_chance", 0.0)
    drawn = session.perform(offline, ledger, QUESTION)

    stages = [payload for name, payload in events if name == "stage"]
    for module in (drawn.rite.question, drawn.rite.world, drawn.rite.reading):
        assert module.name in stages


# A rite chosen instead of drawn

CHAIN = "blind//babel//iching"


def test_a_chosen_rite_runs_exactly_what_was_named(offline, ledger):
    drawn = session.perform(offline, ledger, QUESTION, CHAIN)

    assert [drawn.rite.question.name, drawn.rite.world.name, drawn.rite.reading.name] == [
        "blind",
        "babel",
        "iching",
    ]


def test_a_chosen_rite_is_marked_in_the_ledger(offline, ledger):
    session.perform(offline, ledger, QUESTION, CHAIN)

    assert "(chosen)" in ledger.last().get("Rite")


def test_a_chosen_rite_may_repeat_a_question(offline, ledger):
    session.perform(offline, ledger, QUESTION, CHAIN)
    session.perform(offline, ledger, QUESTION, "blind//babel//cutup")

    assert len(ledger.entries()) == 2
    assert ledger.chain_ok()


def test_a_drawn_rite_still_spends_the_question_after_a_chosen_one(offline, ledger):
    session.perform(offline, ledger, QUESTION, CHAIN)

    with pytest.raises(session.AlreadyAsked):
        session.perform(offline, ledger, QUESTION)


def test_a_question_from_yesterday_is_asked_again_from_the_start(offline, ledger):
    first = session.perform(offline, ledger, QUESTION)
    moved = (datetime.now(timezone.utc).astimezone() - timedelta(hours=25)).isoformat(
        timespec="seconds"
    )
    first.entry.headers["Date"] = moved
    first.entry.headers["Commit"] = seal(
        first.entry.get("Prev"), first.entry.get("Question"), moved
    )
    ledger._write(first.entry)

    session.perform(offline, ledger, QUESTION)

    assert len(ledger.entries()) == 2
    assert ledger.chain_ok()


def test_the_hold_can_be_made_permanent_again(offline, ledger):
    offline.config.set("ledger.repeat_after_h", 0)
    session.perform(offline, ledger, QUESTION)

    with pytest.raises(session.AlreadyAsked):
        session.perform(offline, ledger, QUESTION)


# When a module cannot answer, another one is drawn


@pytest.fixture
def two_worlds(temporary_slot, offline):
    """One question rite, two worlds, one reading, so the fallback is visible."""
    from heidr import registry
    from heidr.contracts import Key

    registry.question("q")(lambda ctx, text: Key(seed=1, anchors=()))
    registry.reading("r")(lambda ctx, text, material: iter(["said"]))
    offline.config.set("rite.silence_chance", 0.0)
    return registry


def test_a_world_that_refuses_gives_way_to_another(two_worlds, offline, ledger):
    from heidr.contracts import Material, Unavailable

    def refuses(ctx, key):
        raise Unavailable("the feed did not answer")

    two_worlds.world("first")(refuses)
    two_worlds.world("second")(lambda ctx, key: Material("found at last", source="second"))

    drawn = session.perform(offline, ledger, QUESTION, "q//first//r")

    assert drawn.material.text == "found at last"
    assert ledger.last().get("Status") == "complete"


def test_a_feed_that_will_not_parse_gives_way_too(two_worlds, offline, ledger):
    from heidr.contracts import Material

    two_worlds.world("first")(lambda ctx, key: {"nothing": 1}["mrkl_root"])
    two_worlds.world("second")(lambda ctx, key: Material("found at last", source="second"))
    drawn = session.perform(offline, ledger, QUESTION, "q//first//r")

    assert drawn.material.text == "found at last"


def test_a_world_that_answers_with_nothing_gives_way(two_worlds, offline, ledger):
    from heidr.contracts import Material

    two_worlds.world("first")(lambda ctx, key: Material("   ", source="first"))
    two_worlds.world("second")(lambda ctx, key: Material("found at last", source="second"))
    drawn = session.perform(offline, ledger, QUESTION, "q//first//r")

    assert drawn.material.text == "found at last"


def test_what_gave_way_is_named_in_the_draw_and_the_entry(two_worlds, offline, ledger):
    from heidr.contracts import Material, Unavailable

    two_worlds.world("first")(lambda ctx, key: (_ for _ in ()).throw(Unavailable("no")))
    two_worlds.world("second")(lambda ctx, key: Material("found at last", source="second"))

    drawn = session.perform(offline, ledger, QUESTION, "q//first//r")

    assert drawn.instead == ("first",)
    assert ledger.last().get("Instead") == "first"
    assert "second" in ledger.last().get("Rite")
    assert ledger.chain_ok()


def test_the_rite_gives_up_when_no_module_is_left(two_worlds, offline, ledger):
    from heidr.contracts import Unavailable

    two_worlds.world("first")(lambda ctx, key: (_ for _ in ()).throw(Unavailable("busy dongle")))

    with pytest.raises(session.NothingAnswered) as refused:
        session.perform(offline, ledger, QUESTION, "q//first//r")

    assert refused.value.slot == "world"
    assert "busy dongle" in refused.value.reason
    assert ledger.asked_before(QUESTION) is None


def test_no_more_attempts_than_the_setting_allows(two_worlds, offline, ledger):
    from heidr.contracts import Unavailable

    tried = []

    def refuses(ctx, key, name=""):
        tried.append(name)
        raise Unavailable("no")

    for name in ("first", "second", "third", "fourth"):
        two_worlds.world(name)(lambda ctx, key, name=name: refuses(ctx, key, name))
    offline.config.set("rite.attempts", 2)

    with pytest.raises(session.NothingAnswered):
        session.perform(offline, ledger, QUESTION, "q//first//r")

    assert len(tried) == 2


def test_stopping_is_not_a_module_giving_way(two_worlds, offline, ledger):
    from heidr.contracts import Cancelled

    two_worlds.world("first")(lambda ctx, key: (_ for _ in ()).throw(Cancelled()))
    two_worlds.world("second")(lambda ctx, key: 1 / 0)

    with pytest.raises(Cancelled):
        session.perform(offline, ledger, QUESTION, "q//first//r")


# The reading is the slot that can fail halfway through a sentence


@pytest.fixture
def two_readings(temporary_slot, offline):
    from heidr import registry
    from heidr.contracts import Key, Material

    registry.question("q")(lambda ctx, text: Key(seed=1, anchors=()))
    registry.world("w")(lambda ctx, key: Material("found", source="fake"))
    offline.config.set("rite.silence_chance", 0.0)
    return registry


def test_a_reading_that_breaks_before_speaking_gives_way(two_readings, offline, ledger):
    two_readings.reading("first")(lambda ctx, text, material: (_ for _ in ()).throw(OSError("no")))
    two_readings.reading("second")(lambda ctx, text, material: iter(["the second one spoke"]))

    drawn = session.perform(offline, ledger, QUESTION, "q//w//first")

    assert drawn.lines == ["the second one spoke"]


def test_a_reading_that_breaks_after_speaking_keeps_what_it_said(two_readings, offline, ledger):
    """Running it again would say the first line twice."""

    def halfway(ctx, text, material):
        yield "the first line"
        raise OSError("and then the connection went")

    two_readings.reading("first")(halfway)
    two_readings.reading("second")(lambda ctx, text, material: iter(["never reached"]))

    drawn = session.perform(offline, ledger, QUESTION, "q//w//first")

    assert drawn.lines == ["the first line"]
    assert drawn.instead == ()


def test_a_reading_that_says_nothing_gives_way(two_readings, offline, ledger):
    two_readings.reading("first")(lambda ctx, text, material: iter(()))
    two_readings.reading("second")(lambda ctx, text, material: iter(["said"]))

    drawn = session.perform(offline, ledger, QUESTION, "q//w//first")

    assert drawn.lines == ["said"]
    assert drawn.instead == ("first",)


def test_a_reading_that_means_its_silence_never_gives_way(two_readings, offline, ledger):
    two_readings.reading("hush", silent=True)(lambda ctx, text, material: iter(()))
    two_readings.reading("second")(lambda ctx, text, material: iter(["not wanted"]))

    drawn = session.perform(offline, ledger, QUESTION, "q//w//hush")

    assert drawn.lines == []
    assert drawn.instead == ()
    assert ledger.last().get("Status") == "complete"
    # Silence is an answer, so the question is spent by it.
    assert ledger.asked_before(QUESTION) is not None


def test_a_rite_nobody_could_read_frees_the_question(two_readings, offline, ledger):
    two_readings.reading("first")(lambda ctx, text, material: iter(()))

    with pytest.raises(session.NothingAnswered):
        session.perform(offline, ledger, QUESTION, "q//w//first")

    assert ledger.last().get("Status") == "broken"
    assert ledger.asked_before(QUESTION) is None
