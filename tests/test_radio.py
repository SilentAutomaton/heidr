import random

import numpy as np
import pytest

from heidr import audio, radio, registry
from heidr.contracts import Key, Unavailable
from heidr.stt.base import Partial

BAND = "88.0-108.0"


def ready(ctx, name: str):
    found = registry.MODULES["world"][name]
    return found, ctx.for_module(name, found.defaults)


class FakeSpeech:
    name = "fake"

    def __init__(self, phrases):
        self.phrases = phrases
        self.blocks = 0

    def available(self):
        return True

    def transcribe(self, blocks):
        self.blocks = len(list(blocks))
        for phrase in self.phrases:
            yield Partial(phrase, final=True)


# Sweep planning


def test_forward_and_backward_are_the_same_stops_in_opposite_order():
    rng = random.Random(1)
    up = radio.plan(BAND, "forward", 5, rng)
    down = radio.plan(BAND, "backward", 5, rng)

    assert up == down[::-1]
    assert up[0] == 88e6 and up[-1] == 108e6


def test_bounce_goes_up_and_comes_back():
    stops = radio.plan(BAND, "bounce", 5, random.Random(1))

    assert stops[0] == 88e6
    assert max(stops) == stops[2]
    assert stops[0] == stops[-1]


def test_random_stays_inside_the_band_and_repeats_nothing():
    stops = radio.plan(BAND, "random", 12, random.Random(7))

    assert len(set(stops)) == 12
    assert all(88e6 <= frequency <= 108e6 for frequency in stops)


def test_a_single_stop_is_allowed():
    assert len(radio.plan(BAND, "forward", 1, random.Random(1))) == 1


def test_the_band_is_read_in_megahertz():
    assert radio.band_edges("3.9-4.0") == (3.9e6, 4.0e6)


# Anchors


def test_phrases_carrying_a_question_word_are_preferred():
    said = ["the weather at noon", "traffic on the bridge", "roof repairs continue"]

    assert radio.matching(said, ("roof",)) == ["roof repairs continue"]


def test_when_nothing_matches_everything_is_kept():
    said = ["the weather at noon"]

    assert radio.matching(said, ("roof",)) == said


def test_without_anchors_nothing_is_filtered():
    said = ["one", "two"]

    assert radio.matching(said, ()) == said


# Downsampling


def test_downsampling_shortens_the_block_by_the_factor():
    block = np.arange(16, dtype=np.float32)

    assert radio.downsample(block, 2).size == 8
    assert radio.downsample(block, 1).size == 16


def test_downsampling_keeps_the_shape_of_a_ramp():
    block = np.arange(8, dtype=np.float32)

    assert list(radio.downsample(block, 2)) == [0.5, 2.5, 4.5, 6.5]


# The whole sweep


def test_a_sweep_plays_transcribes_and_reports(stub_context, events, monkeypatch):
    ctx = stub_context.with_capabilities("sdr", "stt")
    ctx.stt = FakeSpeech(["a voice from the band"])
    found, scoped = ready(ctx, "fm_voice")
    scoped.stt = ctx.stt

    tone = np.sin(np.linspace(0, 50, 4096)).astype(np.float32)
    monkeypatch.setattr(radio, "capture", lambda *args, **kwargs: iter([tone, tone]))
    output = audio.Output(audio.Levels(), 32000)

    material = found.run(scoped, Key(seed=3, anchors=()))

    assert material.text == "a voice from the band"
    assert material.extra["stops"] == 6
    assert [name for name, _ in events].count("spectrum") == 12
    assert any(name == "stage" for name, _ in events)
    assert output.stream is None


def test_a_silent_band_still_produces_material(stub_context, monkeypatch):
    ctx = stub_context.with_capabilities("sdr", "stt")
    ctx.stt = FakeSpeech([])
    found, scoped = ready(ctx, "sw_voice")
    scoped.stt = ctx.stt

    quiet = np.zeros(4096, dtype=np.float32)
    monkeypatch.setattr(radio, "capture", lambda *args, **kwargs: iter([quiet]))

    material = found.run(scoped, Key(seed=1))

    assert material.text == ""
    assert material.source == "shortwave"


def test_a_radio_that_gives_nothing_at_all_says_why(stub_context, monkeypatch):
    ctx = stub_context.with_capabilities("sdr", "stt")
    ctx.stt = FakeSpeech([])
    found, scoped = ready(ctx, "fm_voice")
    scoped.stt = ctx.stt

    monkeypatch.setattr(radio, "capture", lambda *args, **kwargs: iter([]))

    with pytest.raises(Unavailable) as refused:
        found.run(scoped, Key(seed=1))

    assert "holding the dongle" in str(refused.value)


def test_voice_modules_need_both_a_radio_and_a_recogniser(stub_context):
    for name in ("fm_voice", "sw_voice"):
        module = registry.MODULES["world"][name]
        assert module.available(stub_context) is False
        assert module.available(stub_context.with_capabilities("sdr")) is False
