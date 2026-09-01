from heidr import registry
from heidr.contracts import Key
from heidr.world import chain, quake, sky


def ready(ctx, name: str):
    found = registry.MODULES["world"][name]
    return found, ctx.for_module(name, found.defaults)


def online(ctx):
    return ctx.with_capabilities("net")


def test_quake_picks_an_event_by_the_key(stub_context, fake_get, fixture_json):
    fake_get(quake, {"earthquake.usgs.gov": fixture_json("usgs")})
    found, ctx = ready(stub_context, "quake")

    first = found.run(ctx, Key(seed=0))
    second = found.run(ctx, Key(seed=1))

    assert first.text == "14 km NE of Kandilli, Turkey"
    assert second.text == "South of the Fiji Islands"
    assert first.numbers == (34, 7)


def test_quake_survives_a_missing_magnitude(stub_context, fake_get, fixture_json):
    fake_get(quake, {"earthquake.usgs.gov": fixture_json("usgs")})
    found, ctx = ready(stub_context, "quake")

    assert found.run(ctx, Key(seed=2)).numbers == (0, 33)


def test_quake_on_a_quiet_hour_returns_empty_material(stub_context, fake_get, fixture_json):
    fake_get(quake, {"earthquake.usgs.gov": fixture_json("usgs_empty")})
    found, ctx = ready(stub_context, "quake")

    assert found.run(ctx, Key(seed=1)).extra["events"] == 0


def test_chain_reads_the_merkle_root_not_the_block_hash(stub_context, fake_get, fixture_json):
    fake_get(
        chain,
        {"latestblock": fixture_json("latestblock"), "rawblock": fixture_json("rawblock")},
    )
    found, ctx = ready(stub_context, "chain")

    material = found.run(ctx, Key(seed=1))

    assert material.extra["merkle_root"].startswith("9f2c1a4b")
    assert material.numbers[0] == 0x9F2C1A4B


def test_chain_collects_what_people_wrote_into_the_block(stub_context, fake_get, fixture_json):
    fake_get(
        chain,
        {"latestblock": fixture_json("latestblock"), "rawblock": fixture_json("rawblock")},
    )
    found, ctx = ready(stub_context, "chain")

    material = found.run(ctx, Key(seed=1))

    assert "hello from the block!" in material.text
    assert "keep looking" in material.text


def test_chain_ignores_scripts_that_are_not_readable():
    block = {"tx": [{"out": [{"script": "6a04zzzz"}, {"script": "76a914aabb88ac"}]}]}
    assert chain.messages(block, limit=5) == []


def test_sky_stays_out_of_the_lottery_without_a_position(stub_context):
    found = registry.MODULES["world"]["sky"]
    assert found.available(online(stub_context)) is False


def test_sky_joins_once_a_position_is_configured(stub_context):
    stub_context.config.set("modules.sky", {"latitude": 55.75, "longitude": 37.61})
    found = registry.MODULES["world"]["sky"]
    assert found.available(online(stub_context)) is True


def test_sky_prefers_the_callsign_and_falls_back_to_the_registration(
    stub_context, fake_get, fixture_json
):
    fake_get(sky, {"adsb.lol": fixture_json("adsb")})
    found, ctx = ready(stub_context, "sky")

    assert found.run(ctx, Key(seed=0)).text == "RYR52TK"
    assert found.run(ctx, Key(seed=1)).text == "D-AIMA"


def test_sky_with_an_empty_sky_returns_empty_material(stub_context, fake_get, fixture_json):
    fake_get(sky, {"adsb.lol": fixture_json("adsb_empty")})
    found, ctx = ready(stub_context, "sky")

    assert found.run(ctx, Key(seed=0)).extra["aircraft"] == 0


def test_network_modules_are_absent_when_the_network_is(stub_context):
    for name in ("quake", "chain", "sky"):
        assert registry.MODULES["world"][name].available(stub_context) is False
