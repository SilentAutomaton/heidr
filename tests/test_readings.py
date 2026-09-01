import collections
import random

from heidr import registry
from heidr.contracts import Material
from heidr.reading import iching, pythia, tarot

QUESTION = "should the antenna go on the roof"
MATERIAL = Material("a fragment of found text", numbers=(3, 14), source="mojibake")


def ready(ctx, name: str):
    found = registry.MODULES["reading"][name]
    return found, ctx.for_module(name, found.defaults)


# I Ching


def test_the_da_yan_method_gives_the_classical_distribution():
    rng = random.Random(1)
    counted = collections.Counter(iching.cast_line(rng) for _ in range(40000))
    share = {value: counted[value] / 40000 for value in (6, 7, 8, 9)}

    # Old lines are much rarer than young ones. A coin toss would make 6 and 9
    # equal at one eighth each, which is exactly the mistake this avoids.
    assert 0.04 < share[6] < 0.08
    assert 0.28 < share[7] < 0.34
    assert 0.41 < share[8] < 0.47
    assert 0.16 < share[9] < 0.22
    assert share[6] < share[9] < share[7] < share[8]


def test_every_hexagram_pattern_is_in_the_book():
    book = iching.load(iching.CORPUS)
    assert len(book) == 64
    assert {format(number, "06b") for number in range(64)} == set(book)


def test_an_old_line_turns_into_its_opposite():
    values = [9, 7, 8, 6, 7, 8]

    # 9 and 6 are the old lines. They read as yang and yin now, and as their
    # opposites in the hexagram the cast is turning into.
    assert iching.pattern(values) == "110010"
    assert iching.moved(values) == "010110"


def test_iching_names_a_hexagram_and_draws_it(stub_context):
    found, ctx = ready(stub_context, "iching")
    lines = list(found.run(ctx, QUESTION, MATERIAL))

    assert any(line.startswith(("1.", "2.")) or ". " in line for line in lines)
    assert sum(1 for line in lines if line.startswith(("---", "-- "))) == 6


def test_iching_is_decided_by_the_material_not_by_chance(stub_context):
    found, ctx = ready(stub_context, "iching")
    assert list(found.run(ctx, QUESTION, MATERIAL)) == list(found.run(ctx, QUESTION, MATERIAL))


def test_a_different_finding_casts_a_different_hexagram(stub_context):
    found, ctx = ready(stub_context, "iching")
    other = Material("an entirely different fragment", numbers=(1,), source="quake")
    assert list(found.run(ctx, QUESTION, MATERIAL)) != list(found.run(ctx, QUESTION, other))


# Tarot


def test_the_deck_holds_seventy_eight_cards():
    assert len(tarot.load(tarot.DECK)) == 78


def test_a_three_card_spread_names_its_places(stub_context):
    found, ctx = ready(stub_context, "tarot")
    lines = list(found.run(ctx, QUESTION, MATERIAL))

    assert lines[0] == "before"
    assert "now" in lines and "after" in lines


def test_a_one_card_spread_draws_one_card(stub_context):
    found, ctx = ready(stub_context, "tarot")
    ctx.settings["spread"] = "one"
    lines = list(found.run(ctx, QUESTION, MATERIAL))

    assert lines.count("the card") == 1
    assert sum(1 for line in lines if line.startswith("+---")) == 2


def test_no_card_is_drawn_twice(stub_context):
    found, ctx = ready(stub_context, "tarot")
    names = [line.strip("| ") for line in found.run(ctx, QUESTION, MATERIAL) if line.startswith("|")]
    named = [name for name in names if name and name != "reversed"]
    assert len(named) == len(set(named))


def test_reversals_can_be_switched_off(stub_context):
    found, ctx = ready(stub_context, "tarot")
    ctx.settings["reversals"] = False
    assert "reversed" not in " ".join(found.run(ctx, QUESTION, MATERIAL))


# Pythia


class FakeProvider:
    name = "fake"

    def __init__(self):
        self.sent = None

    def stream(self, messages):
        self.sent = messages
        yield "a "
        yield "sign"


def test_pythia_stays_out_of_the_lottery_without_a_provider(stub_context):
    assert registry.MODULES["reading"]["pythia"].available(stub_context) is False


def test_pythia_streams_what_the_model_says(stub_context):
    provider = FakeProvider()
    ctx = stub_context.with_capabilities("llm")
    ctx.llm = provider
    found, scoped = ready(ctx, "pythia")

    assert "".join(found.run(scoped, QUESTION, MATERIAL)) == "a sign"


def test_pythia_sends_the_finding_and_the_question_only(stub_context):
    provider = FakeProvider()
    ctx = stub_context.with_capabilities("llm")
    ctx.llm = provider
    found, scoped = ready(ctx, "pythia")
    list(found.run(scoped, QUESTION, MATERIAL))

    system, user = provider.sent
    assert system.role == "system"
    assert "Do not invent further findings" in system.content
    assert QUESTION in user.content
    assert MATERIAL.text in user.content


def test_pythia_asks_for_the_language_of_the_question(stub_context):
    """A Russian question was coming back answered in English."""
    assert "language of the question" in pythia.INSTRUCTION


def test_pythia_never_invites_the_model_to_refuse(stub_context):
    """Told to use only the fragment, an honest model refuses to read noise."""
    assert "random" in pythia.INSTRUCTION and "Never say" in pythia.INSTRUCTION


def test_a_wall_of_material_reaches_the_model_shortened(stub_context):
    provider = FakeProvider()
    ctx = stub_context.with_capabilities("llm")
    ctx.llm = provider
    ctx.config.set("llm.fragment_chars", 100)
    found, scoped = ready(ctx, "pythia")
    list(found.run(scoped, QUESTION, Material("x" * 4000, source="noise")))

    _system, user = provider.sent
    assert user.content.count("x") == 100
    assert "the first 100 characters of 4000" in user.content


def test_the_voice_follows_the_finding():
    assert pythia.voice_for(MATERIAL) == pythia.voice_for(MATERIAL)
    voices = {pythia.voice_for(Material(f"text {n}", source="s")) for n in range(40)}
    assert len(voices) > 1
