from heidr import net
from heidr.contracts import Key, Material
from heidr.registry import world

FEED = "https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist}"


def available(ctx) -> bool:
    # Without a position there is no overhead to look at, so the module stays
    # out of the lottery until latitude and longitude are configured.
    return ctx.has("net") and bool(ctx.settings.get("latitude")) and bool(ctx.settings.get("longitude"))


def describe(aircraft: dict) -> str:
    callsign = (aircraft.get("flight") or "").strip()
    return callsign or aircraft.get("r") or aircraft.get("hex", "unknown")


@world(
    "sky",
    needs=("net",),
    defaults={"latitude": 0.0, "longitude": 0.0, "radius_nm": 50, "timeout": 10},
)
def run(ctx, key: Key) -> Material:
    url = FEED.format(
        lat=ctx.settings["latitude"],
        lon=ctx.settings["longitude"],
        dist=ctx.settings["radius_nm"],
    )
    flying = net.fetch_json(url, timeout=ctx.settings["timeout"]).get("ac", [])
    if not flying:
        return Material("", (), "adsb.lol", {"aircraft": 0})

    aircraft = flying[key.seed % len(flying)]
    name = describe(aircraft)
    altitude = aircraft.get("alt_baro") or 0
    track = aircraft.get("track") or 0

    ctx.emit("stage", f"sky {name}")
    return Material(
        text=name,
        numbers=(int(altitude) if isinstance(altitude, (int, float)) else 0, int(track)),
        source="adsb.lol",
        extra={
            "altitude_ft": altitude,
            "track_deg": track,
            "type": aircraft.get("t", ""),
            "aircraft": len(flying),
        },
    )
