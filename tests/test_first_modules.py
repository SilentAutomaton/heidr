import pytest

from heidr import registry
from heidr.contracts import Key, Material


QUESTION = "should the antenna go on the roof"


def module(slot: str, name: str):
    return registry.MODULES[slot][name]


def ready(ctx, slot: str, name: str):
    found = module(slot, name)
    return found, ctx.for_module(name, found.defaults)


def test_gematria_is_deterministic_and_keeps_the_longest_words(stub_context):
    found, ctx = ready(stub_context, "question", "gematria")
    first = found.run(ctx, QUESTION)
    assert first == found.run(ctx, QUESTION)
    assert "antenna" in first.anchors


def test_gematria_ignores_punctuation_and_case(stub_context):
    found, ctx = ready(stub_context, "question", "gematria")
    assert found.run(ctx, "Rain?").seed == found.run(ctx, "rain").seed


def test_blind_uses_only_the_length(stub_context):
    found, ctx = ready(stub_context, "question", "blind")
    assert found.run(ctx, "abcde").seed == found.run(ctx, "vwxyz").seed
    assert found.run(ctx, "abcde").anchors == ()


def test_mojibake_returns_readable_runs(stub_context, events):
    found, ctx = ready(stub_context, "world", "mojibake")
    material = found.run(ctx, Key(seed=3))

    assert material.source.startswith("urandom/")
    assert material.extra["runs"] == len(material.text.split())
    assert any(name == "stage" for name, _ in events)


def test_mojibake_encoding_follows_the_key(stub_context):
    found, ctx = ready(stub_context, "world", "mojibake")
    encodings = {found.run(ctx, Key(seed=seed)).extra["encoding"] for seed in range(5)}
    assert len(encodings) > 1


def test_cutup_reuses_only_the_words_it_was_given(stub_context):
    found, ctx = ready(stub_context, "reading", "cutup")
    material = Material("alpha beta gamma delta epsilon zeta eta theta")

    produced = " ".join(found.run(ctx, QUESTION, material)).split()

    assert set(produced) <= set(material.text.split())
    assert produced


def test_cutup_on_empty_material_says_nothing(stub_context):
    found, ctx = ready(stub_context, "reading", "cutup")
    assert list(found.run(ctx, QUESTION, Material(""))) == []


def test_oblique_draws_one_card_from_the_deck(stub_context):
    found, ctx = ready(stub_context, "reading", "oblique")
    lines = list(found.run(ctx, QUESTION, Material("some words", numbers=(1, 2))))
    assert len(lines) == 1


def test_oblique_can_read_another_deck(stub_context, tmp_path):
    deck = tmp_path / "deck.txt"
    deck.write_text("# comment\nonly card\n\n")
    found, ctx = ready(stub_context, "reading", "oblique")
    ctx.settings["deck"] = str(deck)

    assert list(found.run(ctx, QUESTION, Material("x"))) == ["only card"]


def test_mute_yields_nothing(stub_context):
    found, ctx = ready(stub_context, "reading", "mute")
    assert list(found.run(ctx, QUESTION, Material("anything"))) == []


@pytest.mark.parametrize("slot,name", [("question", "gematria"), ("question", "blind")])
def test_question_modules_survive_an_empty_question(stub_context, slot, name):
    found, ctx = ready(stub_context, slot, name)
    assert isinstance(found.run(ctx, ""), Key)
