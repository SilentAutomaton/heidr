import hashlib
import os
import subprocess
import time

import requests

from heidr.contracts import Unavailable

BEACON = "https://beacon.nist.gov/beacon/2.0/pulse/last"
LATEST_BLOCK = "https://blockchain.info/latestblock"
BLOCK = "https://blockchain.info/rawblock/{hash}"
EMPTY_FREQUENCY = "88000000"


def von_neumann(data: bytes) -> tuple[bytes, bytes]:
    """Debias a raw stream: 01 becomes 0, 10 becomes 1, equal pairs are dropped.

    Adapted from rtl-entropy by Paul Warren, GPL-3.0.
    https://github.com/pwarren/rtl-entropy
    """
    accepted = bytearray()
    rejected = bytearray()
    accepted_bits = 0
    accepted_byte = 0
    for byte in data:
        for shift in range(0, 8, 2):
            pair = (byte >> shift) & 0b11
            if pair in (0b00, 0b11):
                rejected.append(pair)
                continue
            accepted_byte = (accepted_byte << 1) | (pair & 1)
            accepted_bits += 1
            if accepted_bits == 8:
                accepted.append(accepted_byte)
                accepted_bits = 0
                accepted_byte = 0
    return bytes(accepted), bytes(rejected)


def whiten(accepted: bytes, rejected: bytes) -> bytes:
    """Fold the discarded pairs back in through SHA-512, as rtl-entropy does.

    The pairs Von Neumann throws away still carry entropy; hashing them and
    mixing the digest into the accepted stream keeps it instead of wasting it.
    """
    if not accepted:
        return hashlib.sha512(rejected).digest()
    mask = hashlib.sha512(rejected).digest()
    stretched = (mask * (len(accepted) // len(mask) + 1))[: len(accepted)]
    return bytes(a ^ b for a, b in zip(accepted, stretched))


def radio_noise(seconds: float = 2.0, frequency: str = EMPTY_FREQUENCY) -> bytes:
    samples = str(int(2_048_000 * seconds))
    command = ["rtl_sdr", "-f", frequency, "-n", samples, "-"]
    finished = subprocess.run(command, capture_output=True, timeout=seconds + 10)
    if not finished.stdout:
        raise Unavailable(busy_message(finished.stderr))
    return finished.stdout


def busy_message(stderr: bytes) -> str:
    """Say why the radio gave nothing, in the words the radio used."""
    said = stderr.decode("utf-8", errors="ignore").strip().splitlines()
    last = said[-1] if said else "the receiver returned no samples"
    if "claim_interface" in " ".join(said) or "Failed to open" in " ".join(said):
        return (
            f"The radio gave nothing: {last} "
            "Another program is holding the dongle. Close it, then draw again."
        )
    return f"The radio gave nothing: {last} Check the antenna and the dongle, then draw again."


def beacon_pulse(timeout: float = 5.0) -> bytes:
    reply = requests.get(BEACON, timeout=timeout, headers={"Accept": "application/json"})
    return reply.json()["pulse"]["outputValue"].encode()


def merkle_root(timeout: float = 5.0) -> bytes:
    # The block hash loses entropy as mining difficulty pushes leading zeros
    # into it. The Merkle root does not. Pointed out by callebtc/randombtc.
    latest = requests.get(LATEST_BLOCK, timeout=timeout).json()["hash"]
    block = requests.get(BLOCK.format(hash=latest), timeout=timeout).json()
    return block["mrkl_root"].encode()


def world_seed(sources: list[bytes] | None = None) -> int:
    """Mix every source that answered into one number.

    Nothing here is trusted alone: a source that fails is simply absent, and
    os.urandom is always present so the mix is never empty.
    """
    digest = hashlib.sha512()
    for source in sources or []:
        digest.update(source)
    digest.update(str(time.time_ns()).encode())
    digest.update(os.urandom(32))
    return int.from_bytes(digest.digest(), "big")


def collect(ctx, seconds: float = 2.0) -> list[bytes]:
    sources: list[bytes] = []
    if ctx.has("sdr"):
        _append(sources, lambda: whiten(*von_neumann(radio_noise(seconds))))
    if ctx.has("net"):
        _append(sources, beacon_pulse)
        _append(sources, merkle_root)
    return sources


def _append(sources: list[bytes], produce) -> None:
    try:
        sources.append(produce())
    except Exception:
        # A source that cannot answer today is not an error; the mix goes on
        # without it.
        pass
