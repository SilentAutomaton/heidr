from datetime import date, datetime, timezone

import pytest

from heidr import registry
from heidr.contracts import Key
from heidr.question import calendar, embed, moment, planetary, words

QUESTION = "should the antenna go on the roof this autumn"


def ready(ctx, name: str):
    found = registry.MODULES["question"][name]
    return found, ctx.for_module(name, found.defaults)


# Shared word handling


def test_words_are_taken_without_punctuation_or_digits():
    assert words.words("Roof, or 2 roofs?") == ["roof", "or", "roofs"]


def test_rarity_prefers_the_less_ordinary_word():
    assert words.rarity("щуплый") > words.rarity("это")
    assert words.rarity("jazz") > words.rarity("the")


# skeleton, acrostic, rarest


def test_the_skeleton_keeps_consonants_and_drops_vowels(stub_context):
    found, ctx = ready(stub_context, "skeleton")

    key = found.run(ctx, "крыша или чердак")

    assert key.anchors == ("крш", "л")


def test_the_skeleton_of_a_vowel_only_word_disappears(stub_context):
    found, ctx = ready(stub_context, "skeleton")

    assert found.run(ctx, "аиоу").anchors == ()


def test_the_acrostic_reads_the_first_letters(stub_context):
    found, ctx = ready(stub_context, "acrostic")

    assert found.run(ctx, "should the antenna go").anchors == ("stag",)


def test_the_rarest_word_becomes_the_only_anchor(stub_context):
    found, ctx = ready(stub_context, "rarest")

    key = found.run(ctx, "is the jazz on the radio")

    assert key.anchors == ("jazz",)


def test_a_question_with_no_words_still_gives_a_key(stub_context):
    for name in ("skeleton", "acrostic", "rarest"):
        found, ctx = ready(stub_context, name)
        assert isinstance(found.run(ctx, "?? 123"), Key)


# moment


def test_the_moon_runs_through_every_phase():
    seen = {moment.phase_name(day * moment.SYNODIC_DAYS / 16) for day in range(16)}

    assert len(seen) == len(moment.PHASES)


def test_a_new_moon_is_called_one():
    assert moment.phase_name(0.0) == "new moon"
    assert moment.phase_name(moment.SYNODIC_DAYS / 2) == "full moon"


def test_the_moment_rite_ignores_the_question(stub_context):
    found, ctx = ready(stub_context, "moment")

    first = found.run(ctx, "one question")
    second = found.run(ctx, "a completely different question")

    assert first.anchors == second.anchors


# calendar


def test_the_long_count_agrees_with_the_famous_date():
    assert calendar.long_count(date(2012, 12, 21)) == "13.0.0.0.0"


def test_the_republic_starts_on_its_first_day():
    assert calendar.republican(date(1792, 9, 22)) == "1 Vendémiaire, year 1"


def test_before_the_republic_there_is_no_republican_date():
    assert calendar.republican(date(1700, 1, 1)) == "before the Republic"


def test_a_leap_day_is_saint_tibs_day():
    assert calendar.discordian(date(2024, 2, 29)).startswith("St Tib's Day")


def test_the_discordian_year_counts_from_the_curse():
    assert calendar.discordian(date(2026, 9, 1)).endswith("3192 YOLD")


def test_the_calendar_rite_rotates_unless_told_otherwise(stub_context):
    found, ctx = ready(stub_context, "calendar")

    assert found.run(ctx, QUESTION).anchors[0] in calendar.CALENDARS

    ctx.settings["which"] = "long_count"
    assert found.run(ctx, QUESTION).anchors == ("long_count",)


# planetary


def test_the_hour_ruler_walks_the_chaldean_order():
    latitude, longitude = 55.75, 37.61
    noon = datetime(2026, 6, 21, 9, 0, tzinfo=timezone.utc).timestamp()

    planet, hour, daylight = planetary.ruler(noon, latitude, longitude)

    assert planet in planetary.CHALDEAN
    assert 1 <= hour <= 12
    assert daylight is True


def test_midnight_is_not_daylight():
    _planet, _hour, daylight = planetary.ruler(
        datetime(2026, 12, 21, 0, 0, tzinfo=timezone.utc).timestamp(), 55.75, 37.61
    )

    assert daylight is False


def test_consecutive_hours_move_along_the_chain():
    latitude, longitude = 0.0, 0.0
    base = datetime(2026, 3, 21, 7, 0, tzinfo=timezone.utc).timestamp()

    rulers = [planetary.ruler(base + step * 3600, latitude, longitude)[0] for step in range(3)]
    places = [planetary.CHALDEAN.index(name) for name in rulers]

    assert [(places[index + 1] - places[index]) % 7 for index in range(2)] == [1, 1]


def test_the_sun_never_sets_inside_the_polar_circle():
    rising, setting = planetary.solar_events(datetime(2026, 6, 21), 78.0, 15.0)

    assert (rising, setting) == (6.0, 18.0)


def test_planetary_waits_for_a_position(stub_context):
    module = registry.MODULES["question"]["planetary"]
    assert module.available(stub_context) is False

    stub_context.config.set("modules.planetary", {"latitude": 55.75, "longitude": 37.61})
    assert module.available(stub_context) is True


# embed


def test_a_vector_folds_into_a_number():
    assert embed.fold([0.5, -0.25, 0.125]) > 0
    assert embed.fold([]) == 0


def test_the_same_vector_always_folds_the_same_way():
    assert embed.fold([0.1, 0.2]) == embed.fold([0.1, 0.2])
    assert embed.fold([0.1, 0.2]) != embed.fold([0.1, 0.3])


def test_embed_waits_for_a_local_daemon(stub_context):
    module = registry.MODULES["question"]["embed"]
    assert module.available(stub_context) is False


def test_embed_falls_back_when_the_vector_is_empty(stub_context, monkeypatch):
    monkeypatch.setattr(embed, "embedding", lambda *args, **kwargs: [])
    found, ctx = ready(stub_context, "embed")

    assert isinstance(found.run(ctx, QUESTION), Key)


def test_embed_uses_the_vector_when_there_is_one(stub_context, monkeypatch):
    monkeypatch.setattr(embed, "embedding", lambda *args, **kwargs: [0.1, 0.2, 0.3])
    found, ctx = ready(stub_context, "embed")

    key = found.run(ctx, QUESTION)

    assert key.seed == embed.fold([0.1, 0.2, 0.3])


# reversal


def test_reversal_waits_for_a_model(stub_context):
    assert registry.MODULES["question"]["reversal"].available(stub_context) is False


def test_reversal_keys_on_what_the_model_said(stub_context):
    class Provider:
        name = "fake"

        def stream(self, messages):
            yield "should the antenna stay off the roof"

    stub_context.llm = Provider()
    found, ctx = ready(stub_context.with_capabilities("llm"), "reversal")
    ctx.llm = stub_context.llm

    key = found.run(ctx, QUESTION)

    assert key.anchors == ("should", "the")


@pytest.mark.parametrize("name", ["skeleton", "acrostic", "rarest", "moment", "calendar"])
def test_the_offline_rites_need_nothing(stub_context, name):
    assert registry.MODULES["question"][name].available(stub_context) is True
