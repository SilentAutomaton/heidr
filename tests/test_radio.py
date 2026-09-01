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
    scoped.settings["tuned"] = False

    tone = np.sin(np.linspace(0, 50, 4096)).astype(np.float32)
    monkeypatch.setattr(radio, "capture", lambda *args, **kwargs: iter([tone, tone]))
    output = audio.Output(audio.Levels(), 32000)

    material = found.run(scoped, Key(seed=3, anchors=()))

    assert material.text == "a voice from the band"
    assert material.extra["stops"] == scoped.settings["stops"]
    assert [name for name, _ in events].count("spectrum") == 2 * scoped.settings["stops"]
    assert any(name == "stage" for name, _ in events)
    assert output.stream is None


def test_a_tuned_sweep_dwells_only_where_the_scan_found_carriers(stub_context, events, monkeypatch):
    ctx = stub_context.with_capabilities("sdr", "stt")
    ctx.stt = FakeSpeech(["one clear station"])
    found, scoped = ready(ctx, "fm_voice")
    scoped.stt = ctx.stt

    monkeypatch.setattr(radio, "scan", lambda band, step, seconds, **kwargs: SWEEP_CSV)
    visited = []

    def capture(frequency, mode, rate, seconds, **kwargs):
        visited.append(frequency)
        return iter([np.zeros(4096, dtype=np.float32)])

    monkeypatch.setattr(radio, "capture", capture)

    found.run(scoped, Key(seed=3))

    assert sorted(visited) == [88300000.0, 88800000.0]
    assert any("scan found 2 carriers" in str(payload) for name, payload in events if name == "stage")


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

    scoped.settings["tuned"] = False
    monkeypatch.setattr(radio, "capture", lambda *args, **kwargs: iter([]))

    with pytest.raises(Unavailable) as refused:
        found.run(scoped, Key(seed=1))

    assert "holding the dongle" in str(refused.value)


def test_voice_modules_need_both_a_radio_and_a_recogniser(stub_context):
    for name in ("fm_voice", "sw_voice"):
        module = registry.MODULES["world"][name]
        assert module.available(stub_context) is False
        assert module.available(stub_context.with_capabilities("sdr")) is False


SWEEP_CSV = """\
2026-09-01, 06:00:00, 88000000, 88300000, 100000.00, 40, 1.0, 1.2, 0.8
2026-09-01, 06:00:00, 88300000, 88600000, 100000.00, 40, 14.0, 13.2, 1.1
2026-09-01, 06:00:00, 88600000, 88900000, 100000.00, 40, 0.9, 1.4, 12.5
"""


def test_every_bin_of_a_sweep_is_read():
    bins = radio.power_bins(SWEEP_CSV)

    assert len(bins) == 9
    assert bins[0] == (88000000, 1.0)
    assert bins[3] == (88300000, 14.0)


def test_carriers_stand_above_the_noise_floor():
    found = radio.stations(radio.power_bins(SWEEP_CSV))

    # 88.3 and 88.4 are one transmitter, so only its loudest bin counts.
    assert [hertz for hertz, _power in found] == [88300000, 88800000]


def test_a_wider_separation_merges_more():
    found = radio.stations(radio.power_bins(SWEEP_CSV), separation=1_000_000)

    assert found == [(88300000, 14.0)]


def test_a_quiet_band_yields_no_carriers():
    quiet = "2026-09-01, 06:00:00, 88000000, 88200000, 100000.00, 40, 1.0, 1.1"

    assert radio.stations(radio.power_bins(quiet)) == []
    assert radio.stations([]) == []


def test_bins_the_scanner_could_not_measure_are_dropped():
    unreadable = "2026-09-01, 06:00:00, 88000000, 88200000, 100000.00, 40, nan, 3.0"

    assert radio.power_bins(unreadable) == [(88100000, 3.0)]


def test_a_tuned_sweep_visits_only_the_carriers_found():
    carriers = [95.0e6, 101.0e6, 106.2e6]

    stops = radio.plan(BAND, "forward", 2, random.Random(1), among=carriers)

    assert stops == [95.0e6, 101.0e6]


def test_a_tuned_random_sweep_stays_among_the_carriers():
    carriers = [95.0e6, 101.0e6, 106.2e6]

    stops = radio.plan(BAND, "random", 3, random.Random(4), among=carriers)

    assert sorted(stops) == carriers


def test_a_tuned_sweep_asks_for_more_stops_than_there_are_stations():
    stops = radio.plan(BAND, "forward", 9, random.Random(1), among=[95.0e6])

    assert stops == [95.0e6]


def test_a_scan_that_finds_nothing_leaves_no_stops():
    assert radio.plan(BAND, "forward", 4, random.Random(1), among=[]) == []


def test_the_output_rate_goes_to_the_resampler_not_the_tuner(monkeypatch):
    """rtl_fm's wbfm preset sets the 170 kHz input itself.

    Passing the output rate to -s narrows the input to 32 kHz and demodulates
    hiss instead of a broadcast, which is what this test exists to prevent.
    """
    seen = {}

    class Process:
        stdout = type("S", (), {"read": staticmethod(lambda size: b"")})()

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return None

    def popen(command, **kwargs):
        seen["command"] = command
        return Process()

    monkeypatch.setattr(radio.subprocess, "Popen", popen)
    list(radio.capture(106203125, "wbfm", 32000, 0.0))

    command = seen["command"]
    assert "-s" not in command
    assert command[command.index("-r") + 1] == "32000"
    assert command[command.index("-M") + 1] == "wbfm"


def test_a_narrow_mode_may_ask_for_its_own_input_rate(monkeypatch):
    seen = {}

    class Process:
        stdout = type("S", (), {"read": staticmethod(lambda size: b"")})()

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return None

    monkeypatch.setattr(
        radio.subprocess, "Popen", lambda command, **kwargs: (seen.update(command=command), Process())[1]
    )
    list(radio.capture(3950000, "am", 16000, 0.0, gain="30", input_rate="12k"))

    command = seen["command"]
    assert command[command.index("-s") + 1] == "12k"
    assert command[command.index("-r") + 1] == "16000"
    assert command[command.index("-g") + 1] == "30"


# Bands


def test_one_band_is_used_as_it_is():
    assert radio.choose_band("88.0-108.0", random.Random(1)) == "88.0-108.0"


def test_several_bands_leave_the_choice_to_the_draw():
    bands = ["5.85-6.20", "9.40-9.90", "15.10-15.80"]

    chosen = {radio.choose_band(bands, random.Random(seed)) for seed in range(30)}

    assert chosen <= set(bands)
    assert len(chosen) > 1


def test_no_bands_at_all_is_no_band():
    assert radio.choose_band([], random.Random(1)) == ""


# Direct sampling


def fake_popen(monkeypatch, seen):
    class Process:
        stdout = type("S", (), {"read": staticmethod(lambda size: b"")})()

        def terminate(self):
            return None

        def wait(self, timeout=None):
            return None

    monkeypatch.setattr(
        radio.subprocess,
        "Popen",
        lambda command, **kwargs: (seen.update(command=command), Process())[1],
    )


def test_direct_sampling_is_off_unless_the_receiver_needs_it():
    for name in ("sw_voice", "mw_voice"):
        assert registry.MODULES["world"][name].defaults["direct"] == ""


def test_shortwave_is_sampled_directly(monkeypatch):
    seen = {}
    fake_popen(monkeypatch, seen)

    list(radio.capture(6070000, "am", 16000, 0.0, input_rate="12k", direct="direct2"))

    command = seen["command"]
    assert command[command.index("-E") + 1] == "direct2"


def test_the_scanner_is_told_about_direct_sampling_too(monkeypatch):
    seen = {}

    class Finished:
        stdout = ""

    monkeypatch.setattr(
        radio.subprocess,
        "run",
        lambda command, **kwargs: (seen.update(command=command), Finished())[1],
    )

    radio.scan("0.531-1.602", "9k", 4, direct=True, gain="40")

    assert "-D" in seen["command"]
    assert seen["command"][seen["command"].index("-g") + 1] == "40"


def test_a_band_below_a_megahertz_still_converts_for_the_scanner():
    assert radio.rtl_power_band("0.531-1.602") == "531000:1602000"


# Am modules


def test_the_am_modules_carry_the_settings_shortwave_needs():
    for name in ("sw_voice", "mw_voice"):
        defaults = registry.MODULES["world"][name].defaults
        assert defaults["mode"] == "am"
        assert defaults["dwell_s"] >= 15
        # rtl_fm answers an input rate below this by producing nothing at all,
        # with no error, which cost an evening to find.
        assert int(defaults["input_rate"].rstrip("k")) * 1000 >= radio.MIN_INPUT_HZ


def test_shortwave_carries_several_metre_bands():
    bands = registry.MODULES["world"]["sw_voice"].defaults["band"]

    assert isinstance(bands, list)
    assert len(bands) >= 4


def test_the_am_modules_need_a_radio_and_a_recogniser(stub_context):
    for name in ("sw_voice", "mw_voice"):
        module = registry.MODULES["world"][name]
        assert module.available(stub_context) is False
        assert module.available(stub_context.with_capabilities("sdr")) is False
