import pytest

from heidr import registry
from heidr.contracts import Key, Unavailable
from heidr.world import apt, hline

SWEEP = """\
2026-09-01, 07:00:00, 1420205751, 1420405751, 100000.00, 40, 2.0, 2.2, 1.9
2026-09-01, 07:00:00, 1420405751, 1420605751, 100000.00, 40, 9.5, 2.1, 2.0
"""


def ready(ctx, name: str):
    found = registry.MODULES["world"][name]
    return found, ctx.for_module(name, found.defaults)


# hline


def test_the_sweep_is_centred_on_the_line():
    band = hline.band_around(hline.REST_HZ, 2_000_000)
    low, high = (int(part) for part in band.split(":"))

    assert low < hline.REST_HZ < high
    assert high - low == 2_000_000


def test_a_line_at_rest_is_not_moving():
    assert hline.radial_velocity(hline.REST_HZ) == 0.0


def test_a_lower_frequency_means_moving_away():
    receding = hline.radial_velocity(hline.REST_HZ - 100_000)
    approaching = hline.radial_velocity(hline.REST_HZ + 100_000)

    assert receding > 0 and approaching < 0
    assert round(receding / 1000, 1) == 21.1


def test_the_excess_is_measured_against_the_median():
    hertz, above, floor = hline.excess([(1, 2.0), (2, 2.0), (3, 9.0)])

    assert hertz == 3
    assert floor == 2.0
    assert above == 7.0


def test_an_empty_sweep_has_no_excess():
    assert hline.excess([]) == (0, 0.0, 0.0)


def test_hline_reports_a_velocity(stub_context, monkeypatch):
    monkeypatch.setattr(hline.radio, "scan", lambda *args, **kwargs: SWEEP)
    found, ctx = ready(stub_context, "hline")

    material = found.run(ctx, Key(seed=1))

    assert "km/s" in material.text
    assert material.extra["hertz"] == 1420405751
    assert material.extra["detected"] is True


def test_a_flat_sky_is_reported_as_undetected(stub_context, monkeypatch):
    flat = "2026-09-01, 07:00:00, 1420205751, 1420405751, 100000.00, 40, 2.0, 2.0, 2.0"
    monkeypatch.setattr(hline.radio, "scan", lambda *args, **kwargs: flat)
    found, ctx = ready(stub_context, "hline")

    assert found.run(ctx, Key(seed=1)).extra["detected"] is False


def test_a_receiver_that_says_nothing_is_reported(stub_context, monkeypatch):
    monkeypatch.setattr(hline.radio, "scan", lambda *args, **kwargs: "")
    found, ctx = ready(stub_context, "hline")

    with pytest.raises(Unavailable) as refused:
        found.run(ctx, Key(seed=1))

    assert "1420 MHz" in str(refused.value)


# apt


def test_the_satellites_are_the_ones_still_transmitting():
    assert set(apt.SATELLITES) == {"noaa-15", "noaa-18", "noaa-19"}
    assert all(137_000_000 < hertz < 138_000_000 for hertz in apt.SATELLITES.values())


def test_an_unknown_satellite_is_named_in_the_refusal(stub_context):
    found, ctx = ready(stub_context, "apt")
    ctx.settings["satellite"] = "sputnik"

    with pytest.raises(Unavailable) as refused:
        found.run(ctx, Key(seed=1))

    assert "noaa-19" in str(refused.value)


def test_apt_waits_for_its_decoder(stub_context):
    assert registry.MODULES["world"]["apt"].available(stub_context.with_capabilities("sdr")) in (
        True,
        False,
    )
    assert registry.MODULES["world"]["apt"].available(stub_context) is False


def test_a_recording_with_no_picture_says_to_check_the_pass(stub_context, monkeypatch, tmp_path):
    audio = tmp_path / "pass.wav"
    audio.write_bytes(b"not really audio")
    monkeypatch.setattr(apt, "record", lambda *args, **kwargs: audio)
    monkeypatch.setattr(apt, "decode", lambda *args, **kwargs: False)

    found, ctx = ready(stub_context, "apt")
    ctx.settings["keep_in"] = str(tmp_path / "keep")

    with pytest.raises(Unavailable) as refused:
        found.run(ctx, Key(seed=1))

    assert "pass prediction" in str(refused.value)


def test_a_decoded_pass_hands_over_the_picture(stub_context, monkeypatch, tmp_path):
    audio = tmp_path / "pass.wav"
    audio.write_bytes(b"audio")
    monkeypatch.setattr(apt, "record", lambda *args, **kwargs: audio)

    def decode(_audio, image):
        image.write_bytes(b"png bytes")
        return True

    monkeypatch.setattr(apt, "decode", decode)
    found, ctx = ready(stub_context, "apt")
    ctx.settings["keep_in"] = str(tmp_path / "keep")

    material = found.run(ctx, Key(seed=1))

    assert material.text.endswith(".png")
    assert material.extra["satellite"] == "noaa-19"
