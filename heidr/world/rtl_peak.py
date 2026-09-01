import shutil

from heidr import radio
from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

def available(ctx) -> bool:
    return ctx.has("sdr") and shutil.which("rtl_power") is not None


def strongest(csv: str) -> tuple[int, float]:
    """The loudest bin of an rtl_power sweep."""
    bins = radio.power_bins(csv)
    if not bins:
        return 0, float("-inf")
    return max(bins, key=lambda pair: pair[1])


def sweep(band: str, step: str, seconds: int) -> str:
    return radio.scan(band, step, seconds)


@world("rtl_peak", needs=("sdr",), visual="waterfall", defaults={"band": "88M:108M", "step": "100k", "seconds": 20})
def run(ctx, key: Key) -> Material:
    csv = sweep(ctx.settings["band"], ctx.settings["step"], int(ctx.settings["seconds"]))
    hertz, power = strongest(csv)
    if hertz == 0:
        raise Unavailable(
            "The sweep came back empty. Either another program is holding the "
            "dongle or the band is wrong. Close the other program, then draw again."
        )

    megahertz = hertz / 1e6
    ctx.emit("stage", f"peak {megahertz:.3f} MHz at {power:.1f} dB")
    return Material(
        text=f"{megahertz:.3f} MHz",
        numbers=(hertz, int(power * 10)),
        source="rtl_power",
        extra={"hertz": hertz, "power_db": power, "band": ctx.settings["band"]},
    )
