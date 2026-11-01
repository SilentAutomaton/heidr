import re

import pytest

from heidr import registry
from heidr.contracts import Key, Material
from heidr.world import sortes


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


# Sortes


def test_the_shipped_book_is_clean_stanzas():
    found = sortes.passages(sortes.BOOK.read_text(encoding="utf-8"))

    assert len(found) == 203
    assert not any(re.search(r"\[\d+\]|Gutenberg|^\d+\. ", passage) for passage in found)
    assert found[25].startswith("Heidi they called her")


def test_the_key_chooses_the_stanza(stub_context):
    found = registry.MODULES["world"]["sortes"]
    ctx = stub_context.for_module("sortes", found.defaults)

    first, second = found.run(ctx, Key(seed=0)), found.run(ctx, Key(seed=1))

    assert first.text != second.text
    assert first == found.run(ctx, Key(seed=203))
    assert first.numbers == (1, 203) and first.source == "edda"


def test_another_book_can_be_opened(stub_context, tmp_path):
    book = tmp_path / "virgil.txt"
    book.write_text("# a note\n\nArms and\nthe man.\n\n\nI sing.\n", encoding="utf-8")
    found = registry.MODULES["world"]["sortes"]
    ctx = stub_context.for_module("sortes", {"book": str(book)})

    assert found.run(ctx, Key(seed=0)).text == "Arms and the man."
    assert found.run(ctx, Key(seed=1)).text == "I sing."


def test_an_empty_book_gives_empty_material(stub_context, tmp_path):
    book = tmp_path / "empty.txt"
    book.write_text("# nothing here\n", encoding="utf-8")
    found = registry.MODULES["world"]["sortes"]
    ctx = stub_context.for_module("sortes", {"book": str(book)})

    material = found.run(ctx, Key(seed=5))
    assert (material.text, material.numbers) == ("", ())
