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


def test_a_reading_that_breaks_after_material_still_spends_the_question(offline, ledger, monkeypatch):
    def broken(ctx, drawn, question, material):
        raise RuntimeError("the reading fell over")

    monkeypatch.setattr(session, "_read", broken)

    with pytest.raises(RuntimeError):
        session.perform(offline, ledger, QUESTION)

    assert ledger.last().get("Status") == "broken"
    assert ledger.asked_before(QUESTION) is not None


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
