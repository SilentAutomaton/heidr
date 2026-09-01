import pytest

from heidr import registry
from heidr.contracts import Key


def test_registration_rejects_unknown_capabilities():
    with pytest.raises(ValueError):
        registry.world("bogus", needs=("telepathy",))


def test_animation_registration_rejects_unknown_glyph_level():
    with pytest.raises(ValueError):
        registry.animation("bogus", glyphs="hieroglyphs")


def test_module_is_skipped_when_its_needs_are_not_met(stub_context, temporary_slot):
    @registry.world("needs_radio", needs=("sdr",))
    def run(ctx, key):
        return None

    assert registry.usable("world", stub_context) == []
    assert registry.usable("world", stub_context.with_capabilities("sdr"))[0].name == "needs_radio"


def test_module_probe_can_veto_availability(stub_context, temporary_slot, monkeypatch):
    @registry.world("moody")
    def run(ctx, key):
        return None

    module = registry.MODULES["world"]["moody"]
    monkeypatch.setattr(__import__("sys").modules[module.origin], "available", lambda ctx: False, raising=False)

    assert registry.usable("world", stub_context) == []


def test_user_directory_modules_join_the_lottery(tmp_path, stub_context, temporary_slot):
    (tmp_path / "mine.py").write_text(
        "from heidr.registry import question\n"
        "from heidr.contracts import Key\n"
        "\n"
        "@question('mine')\n"
        "def run(ctx, text):\n"
        "    return Key(len(text))\n"
    )

    registry.discover(user_dir=tmp_path)

    module = registry.MODULES["question"]["mine"]
    assert module.run(stub_context, "abc") == Key(3)


def test_richest_affordable_animation_wins(temporary_slot):
    from heidr.visuals.paint import ASCII, BRAILLE

    @registry.animation("meter", glyphs="ascii")
    def plain(frame):
        return []

    @registry.animation("meter", glyphs="braille")
    def fine(frame):
        return []

    assert registry.pick_animation("meter", "braille").make().ramp == BRAILLE
    assert registry.pick_animation("meter", "blocks").make().ramp == ASCII
    assert registry.pick_animation("meter", "ascii").make().ramp == ASCII
