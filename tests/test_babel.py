from heidr import registry
from heidr.contracts import Key
from heidr.world import babel


def ready(ctx):
    found = registry.MODULES["world"]["babel"]
    return found, ctx.for_module("babel", found.defaults)


def test_the_multiplier_is_invertible():
    assert babel.MULTIPLIER % babel.BASE != 0
    assert (babel.MULTIPLIER * babel.INVERSE) % babel.MODULUS == 1


def test_an_address_round_trips_through_the_text():
    location = 123456789012345678901234567890
    assert babel.decode(babel.encode(location)) == location


def test_every_page_is_exactly_one_page_long():
    assert len(babel.encode(1)) == babel.PAGE


def test_neighbouring_addresses_hold_unrelated_pages():
    first = babel.encode(1000)
    second = babel.encode(1001)
    shared = sum(a == b for a, b in zip(first, second))
    assert shared < babel.PAGE * 0.1


def test_a_word_can_be_traced_back_to_where_it_lives():
    page = babel.page_beginning_with("heidr")
    location = babel.decode(page)

    assert babel.encode(location).startswith("heidr")


def test_the_address_decomposes_into_library_coordinates():
    address = babel.to_address(babel.PAGES * babel.VOLUMES * 3 + 7)

    assert 1 <= address.wall <= babel.WALLS
    assert 1 <= address.shelf <= babel.SHELVES
    assert 1 <= address.volume <= babel.VOLUMES
    assert 1 <= address.page <= babel.PAGES


def test_the_module_finds_the_anchor_at_the_start_of_its_page(stub_context):
    found, ctx = ready(stub_context)

    material = found.run(ctx, Key(seed=1, anchors=("Antenna",)))

    assert material.text.startswith("antenna")
    assert material.extra["anchor"] == "antenna"
    assert material.extra["address"].count(".") == 4
    assert len(material.extra["address"]) > 100


def test_without_an_anchor_the_key_chooses_the_page(stub_context):
    found, ctx = ready(stub_context)

    first = found.run(ctx, Key(seed=11))
    again = found.run(ctx, Key(seed=11))
    other = found.run(ctx, Key(seed=12))

    assert first.text == again.text
    assert first.text != other.text


def test_punctuation_in_the_anchor_is_dropped(stub_context):
    found, ctx = ready(stub_context)
    assert found.run(ctx, Key(seed=1, anchors=("ro-of!",))).extra["anchor"] == "roof"


def test_babel_needs_neither_network_nor_radio(stub_context):
    assert registry.MODULES["world"]["babel"].available(stub_context) is True
