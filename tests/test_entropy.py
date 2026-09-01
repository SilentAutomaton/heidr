import hashlib
import random
import subprocess
import time

import pytest

from heidr import entropy
from heidr.contracts import Unavailable


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


def test_a_radio_that_returns_nothing_is_not_silently_hashed(monkeypatch):
    class Finished:
        stdout = b""
        stderr = b"usb_claim_interface error -6\nFailed to open rtlsdr device #0.\n"

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Finished())

    with pytest.raises(Unavailable) as refused:
        entropy.radio_noise(0.1)

    assert "Another program is holding the dongle" in str(refused.value)


def test_an_unexplained_failure_still_says_what_to_check(monkeypatch):
    class Finished:
        stdout = b""
        stderr = b""

    monkeypatch.setattr(subprocess, "run", lambda *a, **k: Finished())

    with pytest.raises(Unavailable) as refused:
        entropy.radio_noise(0.1)

    assert "Check the antenna" in str(refused.value)


def test_a_slow_source_is_left_behind(stub_context, monkeypatch):
    def slow():
        time.sleep(5)
        return b"too late"

    monkeypatch.setattr(entropy, "beacon_pulse", slow)
    monkeypatch.setattr(entropy, "merkle_root", lambda *a, **k: b"in time")

    started = time.monotonic()
    sources = entropy.collect(stub_context.with_capabilities("net"), budget_s=0.5)

    assert sources == [b"in time"]
    assert time.monotonic() - started < 3


def test_nothing_available_means_nothing_gathered(stub_context):
    assert entropy.collect(stub_context) == []


def test_the_mix_is_never_empty_even_with_no_sources():
    assert entropy.world_seed([]) != entropy.world_seed([])
