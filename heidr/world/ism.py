import json
import shutil
import subprocess

from heidr.contracts import Key, Material
from heidr.registry import world

# The neighbours' weather stations, tyre pressure sensors and doorbells all
# chatter here, to nobody in particular.
BAND = "433.92M"
INTERESTING = ("temperature_C", "humidity", "pressure_kPa", "wind_avg_km_h", "battery_ok")


def available(ctx) -> bool:
    return ctx.has("sdr") and shutil.which("rtl_433") is not None


def readings(lines: str) -> list[dict]:
    found = []
    for line in lines.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            found.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return found


def describe(reading: dict) -> str:
    model = reading.get("model", "unknown")
    parts = [f"{key} {reading[key]}" for key in INTERESTING if key in reading]
    return f"{model}: {', '.join(parts)}" if parts else model


def listen(frequency: str, seconds: int) -> str:
    command = ["rtl_433", "-f", frequency, "-F", "json", "-T", str(seconds)]
    finished = subprocess.run(command, capture_output=True, text=True, timeout=seconds + 30)
    return finished.stdout


@world("ism", needs=("sdr",), defaults={"frequency": BAND, "seconds": 45})
def run(ctx, key: Key) -> Material:
    heard = readings(listen(ctx.settings["frequency"], int(ctx.settings["seconds"])))
    if not heard:
        return Material("", (), "rtl_433", {"devices": 0})

    ctx.emit("stage", f"ism {len(heard)} messages")
    return Material(
        text=" | ".join(describe(reading) for reading in heard[:8]),
        numbers=tuple(int(reading.get("id", 0)) for reading in heard[:4]),
        source="rtl_433",
        extra={"devices": len({reading.get("model", "") for reading in heard}), "messages": len(heard)},
    )
