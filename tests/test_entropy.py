import hashlib
import random

from heidr import entropy


def biased_stream(probability: float, size: int, seed: int) -> bytes:
    rng = random.Random(seed)
    bits = [1 if rng.random() < probability else 0 for _ in range(size * 8)]
    return bytes(
        sum(bit << (7 - index) for index, bit in enumerate(bits[start : start + 8]))
        for start in range(0, len(bits), 8)
    )


def test_von_neumann_removes_a_deliberate_bias():
    # Four ones for every one zero going in; the accepted bits have to come out
    # close to balanced.
    accepted, _ = entropy.von_neumann(biased_stream(0.8, 8192, seed=1))

    ones = sum(bin(byte).count("1") for byte in accepted)
    share = ones / (len(accepted) * 8)
    assert 0.45 < share < 0.55


def test_equal_pairs_are_rejected_and_kept_aside():
    accepted, rejected = entropy.von_neumann(bytes([0b00000000, 0b11111111]))
    assert accepted == b""
    assert len(rejected) == 8


def test_whitening_uses_the_rejected_pairs():
    accepted = bytes(range(64))
    one = entropy.whiten(accepted, b"first")
    other = entropy.whiten(accepted, b"second")
    assert one != other
    assert len(one) == len(accepted)


def test_whitening_an_empty_stream_still_returns_entropy():
    assert entropy.whiten(b"", b"rejected") == hashlib.sha512(b"rejected").digest()


def test_world_seed_differs_between_calls_with_the_same_sources():
    first = entropy.world_seed([b"same"])
    second = entropy.world_seed([b"same"])
    assert first != second


def test_a_failing_source_is_skipped_without_breaking_the_mix(stub_context, monkeypatch):
    monkeypatch.setattr(entropy, "beacon_pulse", lambda *a, **k: 1 / 0)
    monkeypatch.setattr(entropy, "merkle_root", lambda *a, **k: b"root")

    sources = entropy.collect(stub_context.with_capabilities("net"))

    assert sources == [b"root"]
