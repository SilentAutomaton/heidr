import socket
import time

from heidr.contracts import Key, Material
from heidr.registry import world

# dump1090 serves BaseStation format on this port: one comma separated line per
# message, several messages per aircraft, each carrying a different field.
PORT = 30003
HEXIDENT, CALLSIGN, ALTITUDE, TRACK = 4, 10, 11, 13


def available(ctx) -> bool:
    return ctx.has("sdr") and reachable(ctx.settings.get("host", "127.0.0.1"), int(ctx.settings.get("port", PORT)))


def reachable(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except OSError:
        return False


def aircraft_from(feed: str) -> dict[str, dict]:
    """Fold many partial messages into one entry per aircraft."""
    seen: dict[str, dict] = {}
    for line in feed.splitlines():
        fields = line.split(",")
        if len(fields) <= TRACK or fields[0] != "MSG":
            continue
        found = seen.setdefault(fields[HEXIDENT], {"hex": fields[HEXIDENT]})
        if fields[CALLSIGN].strip():
            found["callsign"] = fields[CALLSIGN].strip()
        if fields[ALTITUDE].strip():
            found["altitude"] = int(fields[ALTITUDE])
        if fields[TRACK].strip():
            found["track"] = int(float(fields[TRACK]))
    return seen


def listen(host: str, port: int, seconds: int) -> str:
    collected = []
    deadline = time.monotonic() + seconds
    with socket.create_connection((host, port), timeout=seconds) as feed:
        feed.settimeout(1.0)
        while time.monotonic() < deadline:
            try:
                block = feed.recv(8192)
            except OSError:
                break
            if not block:
                break
            collected.append(block.decode("ascii", errors="ignore"))
    return "".join(collected)


@world("adsb_local", visual="radar", needs=("sdr",), defaults={"host": "127.0.0.1", "port": PORT, "seconds": 45})
def run(ctx, key: Key) -> Material:
    feed = listen(ctx.settings["host"], int(ctx.settings["port"]), int(ctx.settings["seconds"]))
    seen = aircraft_from(feed)
    if not seen:
        return Material("", (), "dump1090", {"aircraft": 0})

    chosen = list(seen.values())[key.seed % len(seen)]
    name = chosen.get("callsign") or chosen["hex"]

    ctx.emit("stage", f"overhead {name}")
    return Material(
        text=name,
        numbers=(chosen.get("altitude", 0), chosen.get("track", 0)),
        source="dump1090",
        extra={**chosen, "aircraft": len(seen)},
    )
