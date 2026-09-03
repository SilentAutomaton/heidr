import hashlib
import shutil

from heidr import entropy
from heidr.contracts import Key, Material
from heidr.registry import world

# A frequency with nothing on it, so what arrives is the noise floor of the
# atmosphere and of the receiver rather than anyone's transmission.
EMPTY = "88000000"


def available(ctx) -> bool:
    return ctx.has("sdr") and shutil.which("rtl_sdr") is not None


def condition(raw: bytes) -> bytes:
    """Debias and whiten the receiver's own noise before trusting it."""
    return entropy.whiten(*entropy.von_neumann(raw))


@world("sdr_noise", needs=("sdr",), visual="bits", defaults={"frequency": EMPTY, "seconds": 3.0})
def run(ctx, key: Key) -> Material:
    raw = entropy.radio_noise(float(ctx.settings["seconds"]), str(ctx.settings["frequency"]))
    clean = condition(raw)
    digest = hashlib.sha512(clean).digest()

    ctx.emit("stage", f"noise {len(raw)} bytes, {len(clean)} kept")
    return Material(
        text="",
        numbers=tuple(int.from_bytes(digest[start : start + 8], "big") for start in range(0, 32, 8)),
        source=f"rtl_sdr/{ctx.settings['frequency']}",
        extra={"raw_bytes": len(raw), "kept_bytes": len(clean), "digest": digest.hex()[:32]},
    )
