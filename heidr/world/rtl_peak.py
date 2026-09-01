import shutil
import subprocess

from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

HEADER = 6


def available(ctx) -> bool:
    return ctx.has("sdr") and shutil.which("rtl_power") is not None


def strongest(csv: str) -> tuple[int, float]:
    """Find the loudest bin in an rtl_power sweep.

    Each line is date, time, low hertz, high hertz, step, sample count, and then
    one power reading per bin across that range.
    """
    best_hertz, best_power = 0, float("-inf")
    for line in csv.splitlines():
        fields = [field.strip() for field in line.split(",")]
        if len(fields) <= HEADER:
            continue
        low, step = int(fields[2]), float(fields[4])
        for index, reading in enumerate(fields[HEADER:]):
            try:
                power = float(reading)
            except ValueError:
                continue
            if power > best_power:
                best_hertz, best_power = int(low + index * step), power
    return best_hertz, best_power


def sweep(band: str, step: str, seconds: int) -> str:
    command = ["rtl_power", "-f", f"{band}:{step}", "-i", str(seconds), "-1", "-"]
    finished = subprocess.run(command, capture_output=True, text=True, timeout=seconds + 30)
    return finished.stdout


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
