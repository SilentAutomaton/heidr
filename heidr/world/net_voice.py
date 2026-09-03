import random
from urllib.parse import urlencode

from heidr import net, stream
from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

# The directory answers on several mirrors and which of them is alive changes;
# the `all.` name round-robins over the ones that are. Resolving the host that
# way, and naming the caller in the User-Agent, are the conventions of pyradios
# by André P. Santos, MIT. https://github.com/andreztz/pyradios
DIRECTORY = "https://all.api.radio-browser.info/json/stations/search"


def available(ctx) -> bool:
    return stream.available(ctx, "ffmpeg")


@world(
    "net_voice",
    needs=("net", "stt"),
    visual="globe",
    defaults={
        "stops": 4,
        "dwell_s": 5,
        "rate": 16000,
        "bins": 64,
        "pool": 20,
        "codec": "MP3",
        "bitrate_min": 64,
        "language": "",
        "tag": "",
    },
)
def run(ctx, key: Key) -> Material:
    stops = _stops_for(ctx, key)
    said, reached = stream.gather(ctx, key, stops)

    return Material(
        text=" / ".join(said),
        numbers=tuple(stop.number for stop in reached[:4]),
        source="internet radio",
        extra={
            "stops": len(reached),
            "phrases": len(said),
            "stations": [stop.label for stop in reached],
        },
    )


def _stops_for(ctx, key: Key) -> list[stream.Stop]:
    found = stations(ctx)
    if not found:
        raise Unavailable(
            "The station directory listed nothing. Its filters may be too "
            "narrow, or it is having a bad day. Widen them with :set, or draw "
            "again later."
        )
    # The directory shuffles for us, but the order a question takes has to come
    # from the question, or the same one would take a different route each time.
    random.Random(key.seed).shuffle(found)
    return [described(station) for station in found]


def stations(ctx) -> list[dict]:
    settings = ctx.settings
    query = {
        "order": "random",
        "hidebroken": "true",
        "limit": max(1, int(settings["pool"])),
    }
    for name in ("codec", "language", "tag"):
        if settings.get(name):
            query[name] = str(settings[name])
    if int(settings.get("bitrate_min", 0)):
        query["bitrate_min"] = int(settings["bitrate_min"])

    listed = net.fetch_json(f"{DIRECTORY}?{urlencode(query)}", headers=stream.NAMED)
    return [station for station in listed if _url(station)]


def described(station: dict) -> stream.Stop:
    name = (station.get("name") or "unnamed station").strip()
    where = (station.get("country") or "").strip()
    return stream.Stop(
        label=f"{name} ({where})" if where else name,
        url=_url(station),
        number=int(station.get("bitrate") or 0),
    )


def _url(station: dict) -> str:
    # `url_resolved` has already followed the playlist the station advertises,
    # which is what makes one ffmpeg enough for all of them.
    return (station.get("url_resolved") or station.get("url") or "").strip()
