import random

import pytest

from heidr import registry, rite
from heidr.contracts import Key, Material, Unavailable


@pytest.fixture
def three_slots(temporary_slot):
    for name in ("alpha", "beta"):
        registry.question(name)(lambda ctx, text, _n=name: Key(len(text)))
        registry.world(name)(lambda ctx, key, _n=name: Material(_n))
        registry.reading(name)(lambda ctx, text, material, _n=name: iter(()))


def test_a_draw_names_one_module_per_slot(stub_context, three_slots):
    drawn = rite.draw(stub_context, seed=1)
    assert {drawn.question.slot, drawn.world.slot, drawn.reading.slot} == {
        "question",
        "world",
        "reading",
    }


def test_the_same_seed_draws_the_same_rite(stub_context, three_slots):
    assert str(rite.draw(stub_context, seed=7)) == str(rite.draw(stub_context, seed=7))


def test_different_seeds_eventually_draw_different_rites(stub_context, three_slots):
    drawn = {str(rite.draw(stub_context, seed=seed)) for seed in range(20)}
    assert len(drawn) > 1


def test_an_empty_slot_stops_the_draw(stub_context, temporary_slot):
    with pytest.raises(rite.NothingAvailable):
        rite.draw(stub_context, seed=1)


def test_recent_modules_lose_weight_without_being_banned():
    modules = list(registry.MODULES["question"].values())
    assert rite.weights([], (), 4) == []

    class Fake:
        def __init__(self, name):
            self.name = name

    pair = [Fake("alpha"), Fake("beta")]
    assert rite.weights(pair, ("alpha",), 4) == [0.25, 1.0]

    picked = {rite.pick(pair, ("alpha",), 4, random.Random(s)).name for s in range(50)}
    assert picked == {"alpha", "beta"}


def test_silence_happens_at_the_configured_rate(stub_context, three_slots):
    stub_context.config.set("rite.silence_chance", 1.0)
    assert rite.draw(stub_context, seed=3).silent is True

    stub_context.config.set("rite.silence_chance", 0.0)
    assert rite.draw(stub_context, seed=3).silent is False


def test_a_rite_prints_as_the_wordmark_separator(stub_context, three_slots):
    assert "//" in str(rite.draw(stub_context, seed=5))


# A rite named rather than drawn


def test_a_named_rite_is_exactly_what_was_named(stub_context, temporary_slot):
    for slot in registry.SLOTS:
        for name in ("first", "second"):
            getattr(registry, slot)(f"{slot}_{name}")(lambda *args: None)

    picked = rite.chosen(stub_context, "question_first//world_second//reading_first", seed=1)

    assert str(picked) == "question_first//world_second//reading_first (chosen)"
    assert picked.chosen is True


def test_a_star_leaves_the_slot_to_the_lottery(stub_context, temporary_slot):
    for slot in registry.SLOTS:
        registry_slot = getattr(registry, slot)
        registry_slot(f"{slot}_only")(lambda *args: None)

    picked = rite.chosen(stub_context, "*//world_only//*", seed=1)

    assert picked.question.name == "question_only"
    assert picked.world.name == "world_only"


def test_a_named_reading_is_never_silenced(stub_context, temporary_slot):
    for slot in registry.SLOTS:
        getattr(registry, slot)(f"{slot}_only")(lambda *args: None)
    stub_context.config.set("rite.silence_chance", 1.0)

    assert rite.chosen(stub_context, "*//*//reading_only", seed=1).silent is False
    assert rite.chosen(stub_context, "*//*//*", seed=1).silent is True


def test_an_unknown_name_says_what_the_names_are(stub_context, temporary_slot):
    for slot in registry.SLOTS:
        getattr(registry, slot)(f"{slot}_only")(lambda *args: None)

    with pytest.raises(Unavailable) as refused:
        rite.chosen(stub_context, "nowhere//world_only//reading_only", seed=1)

    assert "question_only" in str(refused.value)


def test_a_rite_that_is_not_three_names_is_refused(stub_context, temporary_slot):
    with pytest.raises(Unavailable):
        rite.chosen(stub_context, "babel", seed=1)


def test_a_drawn_rite_is_not_marked_as_chosen(stub_context, temporary_slot):
    for slot in registry.SLOTS:
        getattr(registry, slot)(f"{slot}_only")(lambda *args: None)

    assert rite.draw(stub_context, seed=1).chosen is False
    assert "(chosen)" not in str(rite.draw(stub_context, seed=1))
