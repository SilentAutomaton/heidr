import json
import random
import re

from heidr import kiwi, net, radio, stream
from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

# kiwisdr.com/public is behind a browser challenge and cannot be read by a
# program. This mirror is regenerated from it about once an hour and is plain
# JavaScript: one array of receivers, each with its host, bands and free slots.
LIST = "http://rx.linkfanel.net/kiwisdr_com.js"
# The international shortwave broadcast bands, the same ones sw_voice sweeps.
BANDS = (
    "5.85-6.20",
    "7.20-7.45",
    "9.40-9.90",
    "11.60-12.10",
    "15.10-15.80",
)


def available(ctx) -> bool:
    return stream.available(ctx)


@world(
    "kiwi_voice",
    needs=("net", "stt"),
    visual="relay",
    defaults={
        "band": list(BANDS),
        "stops": 3,
        "dwell_s": 6,
        "mode": "am",
        "rate": 16000,
        "bins": 64,
        "pool": 12,
    },
)
def run(ctx, key: Key) -> Material:
    stops = _stops_for(ctx, key)
    mode = str(ctx.settings["mode"])
    said, reached = stream.gather(
        ctx, key, stops, reader=lambda stop, rate, seconds: listen(stop, rate, seconds, mode)
    )

    return Material(
        text=" / ".join(said),
        numbers=tuple(stop.number for stop in reached[:4]),
        source="kiwisdr",
        extra={
            "stops": len(reached),
            "phrases": len(said),
            "receivers": [stop.label for stop in reached],
        },
    )


def listen(stop: stream.Stop, rate: int, seconds: float, mode: str):
    """Audio from one public receiver, over its own socket.

    The receiver speaks WebSocket and nothing else — there is no HTTP endpoint
    for the sound — so `heidr/kiwi.py` talks to it directly rather than through
    a separate program.
    """
    host, port = kiwi.address(stop.url)
    return kiwi.capture(host, port, float(stop.number), mode, rate, seconds, stream.AGENT)


def receivers(text: str) -> list[dict]:
    """The mirror is JavaScript, so the array is lifted out of it.

    It is not quite JSON either: the generator leaves a comma after the last
    entry of a list, which every browser accepts and no JSON reader does.
    """
    opened, closed = text.find("["), text.rfind("]")
    if opened < 0 or closed < opened:
        return []
    body = re.sub(r",\s*(\]|\})", r"\1", text[opened : closed + 1])
    try:
        listed = json.loads(body)
    except json.JSONDecodeError:
        return []
    return [entry for entry in listed if isinstance(entry, dict)]


def listening(entry: dict, hertz: float) -> bool:
    """A receiver that is up, has room, and can reach this frequency."""
    if entry.get("status") != "active" or entry.get("offline") == "yes":
        return False
    if not entry.get("url"):
        return False
    # `ext_api` is the owner's cap on how many of the receiver's channels
    # non-browser clients may take. Zero means they asked programs not to
    # connect at all, and that is an answer, not an obstacle.
    if str(entry.get("ext_api", "")).strip() == "0":
        return False
    # Eight slots is the usual whole allowance of a public receiver, and other
    # people are on it. One that is full is left alone rather than knocked at.
    if _number(entry.get("users")) >= _number(entry.get("users_max"), 0):
        return False
    low, _, high = str(entry.get("bands", "")).partition("-")
    return _number(low, 0) <= hertz <= _number(high, 0)


def _stops_for(ctx, key: Key) -> list[stream.Stop]:
    settings = ctx.settings
    rng = random.Random(key.seed)
    band = radio.choose_band(settings["band"], rng)
    ctx.emit("stage", f"band {band} MHz")
    hertz = _somewhere_in(band, rng)

    listed = receivers(net.fetch_text(LIST, headers=stream.NAMED))
    free = [entry for entry in listed if listening(entry, hertz)]
    if not free:
        raise Unavailable(
            "No public receiver was free on that band. They are other people's "
            "radios and they are all in use. Draw again in a few minutes."
        )
    ctx.emit("stage", f"{len(free)} receivers free")

    rng.shuffle(free)
    # One stop per receiver. Two connections to the same radio would take two of
    # its eight slots to hear the same frequency twice.
    return [described(entry, hertz) for entry in free[: max(1, int(settings["pool"]))]]


def described(entry: dict, hertz: float) -> stream.Stop:
    where = (entry.get("loc") or entry.get("name") or "somewhere").strip()
    return stream.Stop(
        label=f"{hertz / 1e6:.3f} MHz via {where}",
        url=str(entry["url"]),
        number=int(hertz / 1000),
    )


def _somewhere_in(band: str, rng: random.Random) -> float:
    low, high = radio.band_edges(band)
    # On the 5 kHz channel grid the broadcasters actually use.
    steps = max(1, int((high - low) // 5000))
    return low + rng.randrange(steps + 1) * 5000


def _number(value, fallback: int = 10**9) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback
