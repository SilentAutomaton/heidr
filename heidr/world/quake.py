from heidr import net
from heidr.contracts import Key, Material
from heidr.registry import world

FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"


def available(ctx) -> bool:
    return ctx.has("net")


@world("quake", needs=("net",), visual="seismo", defaults={"feed": FEED, "timeout": 10})
def run(ctx, key: Key) -> Material:
    events = net.fetch_json(ctx.settings["feed"], timeout=ctx.settings["timeout"])["features"]
    if not events:
        return Material("", (), "usgs", {"events": 0})

    event = events[key.seed % len(events)]
    place = event["properties"]["place"]
    magnitude = event["properties"]["mag"] or 0.0
    longitude, latitude, depth = event["geometry"]["coordinates"]

    ctx.emit("stage", f"quake {place}")
    return Material(
        text=place,
        numbers=(int(magnitude * 10), int(depth)),
        source="usgs",
        extra={
            "magnitude": magnitude,
            "depth_km": depth,
            "latitude": latitude,
            "longitude": longitude,
            "events": len(events),
        },
    )
