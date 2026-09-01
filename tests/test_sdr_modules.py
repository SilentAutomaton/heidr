import os

from heidr import registry
from heidr.contracts import Key
from heidr.world import adsb_local, ism, rtl_peak, sdr_noise

SWEEP = """\
2026-09-01, 04:00:00, 88000000, 88300000, 100000.00, 40, -41.2, -39.8, -38.1
2026-09-01, 04:00:00, 88300000, 88600000, 100000.00, 40, -37.0, -12.5, -36.4
2026-09-01, 04:00:00, 88600000, 88900000, 100000.00, 40, -40.0, nan, -39.1
"""

SBS = """\
MSG,8,1,1,4CA7B5,1,2026/09/01,04:00:00.000,2026/09/01,04:00:00.000,,,,,,,,,,,
MSG,1,1,1,4CA7B5,1,2026/09/01,04:00:01.000,2026/09/01,04:00:01.000,RYR52TK ,,,,,,,,,,
MSG,3,1,1,4CA7B5,1,2026/09/01,04:00:02.000,2026/09/01,04:00:02.000,,34000,,,55.7,37.6,,,,,
MSG,4,1,1,4CA7B5,1,2026/09/01,04:00:03.000,2026/09/01,04:00:03.000,,,420,271.2,,,,,,,
MSG,1,1,1,3C6444,1,2026/09/01,04:00:04.000,2026/09/01,04:00:04.000,DLH8HK  ,,,,,,,,,,
not a message
"""

RTL433 = """\
rtl_433 version 22.11 starting
{"time":"2026-09-01 04:00:00","model":"Nexus-TH","id":31,"temperature_C":18.4,"humidity":62}
{"broken json
{"time":"2026-09-01 04:00:07","model":"Acurite-Tower","id":4127,"temperature_C":19.1,"battery_ok":1}
"""


def ready(ctx, name: str):
    found = registry.MODULES["world"][name]
    return found, ctx.for_module(name, found.defaults)


# rtl_peak


def test_the_loudest_bin_wins():
    hertz, power = rtl_peak.strongest(SWEEP)

    assert power == -12.5
    assert hertz == 88400000


def test_unreadable_readings_are_skipped():
    assert rtl_peak.strongest("2026-09-01, 04:00:00, 100, 200, 50.00, 10, nan, nan")[1] == float("-inf")


def test_a_sweep_with_no_data_lines_gives_nothing():
    assert rtl_peak.strongest("2026-09-01, 04:00:00, 100") == (0, float("-inf"))


def test_rtl_peak_reports_the_frequency_it_found(stub_context, monkeypatch):
    monkeypatch.setattr(rtl_peak, "sweep", lambda band, step, seconds: SWEEP)
    found, ctx = ready(stub_context, "rtl_peak")

    material = found.run(ctx, Key(seed=1))

    assert material.text == "88.400 MHz"
    assert material.extra["hertz"] == 88400000


# adsb_local


def test_partial_messages_are_folded_into_one_aircraft():
    seen = adsb_local.aircraft_from(SBS)

    assert set(seen) == {"4CA7B5", "3C6444"}
    assert seen["4CA7B5"] == {
        "hex": "4CA7B5",
        "callsign": "RYR52TK",
        "altitude": 34000,
        "track": 271,
    }


def test_lines_that_are_not_messages_are_ignored():
    assert adsb_local.aircraft_from("not a message\nMSG,1\n") == {}


def test_adsb_local_names_an_aircraft_overhead(stub_context, monkeypatch):
    monkeypatch.setattr(adsb_local, "listen", lambda host, port, seconds: SBS)
    found, ctx = ready(stub_context, "adsb_local")

    material = found.run(ctx, Key(seed=0))

    assert material.text == "RYR52TK"
    assert material.extra["aircraft"] == 2


def test_an_empty_sky_gives_empty_material(stub_context, monkeypatch):
    monkeypatch.setattr(adsb_local, "listen", lambda host, port, seconds: "")
    found, ctx = ready(stub_context, "adsb_local")

    assert found.run(ctx, Key(seed=0)).extra["aircraft"] == 0


# ism


def test_only_whole_json_lines_are_kept():
    heard = ism.readings(RTL433)

    assert [reading["model"] for reading in heard] == ["Nexus-TH", "Acurite-Tower"]


def test_a_reading_is_described_by_what_it_carries():
    assert ism.describe({"model": "Nexus-TH", "temperature_C": 18.4, "humidity": 62}) == (
        "Nexus-TH: temperature_C 18.4, humidity 62"
    )
    assert ism.describe({"model": "Mystery"}) == "Mystery"


def test_ism_gathers_the_neighbourhood(stub_context, monkeypatch):
    monkeypatch.setattr(ism, "listen", lambda frequency, seconds: RTL433)
    found, ctx = ready(stub_context, "ism")

    material = found.run(ctx, Key(seed=1))

    assert "Nexus-TH" in material.text and "Acurite-Tower" in material.text
    assert material.extra["devices"] == 2
    assert material.numbers == (31, 4127)


# sdr_noise


def test_receiver_noise_is_debiased_before_it_is_trusted():
    raw = os.urandom(4096)
    assert sdr_noise.condition(raw) != raw


def test_sdr_noise_reports_how_much_survived(stub_context, monkeypatch):
    monkeypatch.setattr("heidr.entropy.radio_noise", lambda seconds, frequency: os.urandom(8192))
    found, ctx = ready(stub_context, "sdr_noise")

    material = found.run(ctx, Key(seed=1))

    assert material.extra["raw_bytes"] == 8192
    assert 0 < material.extra["kept_bytes"] < 8192
    assert len(material.numbers) == 4


# availability


def test_no_radio_means_no_radio_modules(stub_context):
    for name in ("sdr_noise", "rtl_peak", "ism", "adsb_local"):
        assert registry.MODULES["world"][name].available(stub_context) is False
