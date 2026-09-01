import pytest

from heidr import entropy, session
from heidr.ledger import Ledger

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


def test_a_failed_draw_is_recorded_as_void_and_still_blocks(offline, ledger, monkeypatch):
    monkeypatch.setattr(session.rite, "draw", lambda *a, **k: 1 / 0)

    with pytest.raises(ZeroDivisionError):
        session.perform(offline, ledger, QUESTION)

    assert ledger.last().get("Status") == "void"
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
