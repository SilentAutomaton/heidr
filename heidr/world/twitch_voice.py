import os
import random
import subprocess
from typing import Iterator
from urllib.parse import urlencode

import numpy as np

from heidr import net, stream
from heidr.contracts import Key, Material, Unavailable
from heidr.registry import world

TOKEN = "https://id.twitch.tv/oauth2/token"
STREAMS = "https://api.twitch.tv/helix/streams"
CHANNEL = "https://www.twitch.tv/"
ID_ENV = "HEIDR_TWITCH_ID"
SECRET_ENV = "HEIDR_TWITCH_SECRET"
RESOLVE_S = 20.0


def credentials() -> tuple[str, str]:
    return os.environ.get(ID_ENV, ""), os.environ.get(SECRET_ENV, "")


def available(ctx) -> bool:
    return all(credentials()) and stream.available(ctx, "ffmpeg", "yt-dlp")


@world(
    "twitch_voice",
    needs=("net", "stt"),
    visual="waterfall",
    defaults={
        "stops": 2,
        "dwell_s": 5,
        "rate": 16000,
        "bins": 64,
        "pool": 20,
        "language": "en",
    },
)
def run(ctx, key: Key) -> Material:
    stops = _stops_for(ctx, key)
    said, reached = stream.gather(ctx, key, stops, reader=_hear)

    return Material(
        text=" / ".join(said),
        numbers=tuple(stop.number for stop in reached[:4]),
        source="twitch",
        extra={
            "stops": len(reached),
            "phrases": len(said),
            "channels": [stop.label for stop in reached],
        },
    )


def token() -> str:
    client, secret = credentials()
    query = urlencode(
        {"client_id": client, "client_secret": secret, "grant_type": "client_credentials"}
    )
    granted = net.post_json(f"{TOKEN}?{query}", {}).get("access_token", "")
    if not granted:
        raise Unavailable(
            f"Twitch would not grant a token. The values in {ID_ENV} and "
            f"{SECRET_ENV} are wrong or the application was removed. Register "
            "one at dev.twitch.tv, then draw again."
        )
    return granted


def live(ctx, bearer: str) -> list[dict]:
    """Channels broadcasting right now, as the sanctioned interface reports them."""
    settings = ctx.settings
    query = {"first": max(1, int(settings["pool"])), "type": "live"}
    if settings.get("language"):
        query["language"] = str(settings["language"])
    client, _secret = credentials()
    headers = {"Client-Id": client, "Authorization": f"Bearer {bearer}"}
    return net.fetch_json(f"{STREAMS}?{urlencode(query)}", headers=headers).get("data", [])


def described(channel: dict) -> stream.Stop:
    name = (channel.get("user_name") or channel.get("user_login") or "").strip()
    return stream.Stop(
        label=name,
        url=str(channel.get("user_login") or name).lower(),
        number=int(channel.get("viewer_count") or 0),
    )


def resolve(channel: str) -> str:
    """The channel page becomes a playlist URL, or nothing if it went dark.

    yt-dlp answers a channel that stopped broadcasting between the listing and
    now by saying so rather than by hanging, which is what makes it usable here.
    """
    finished = subprocess.run(
        ["yt-dlp", "-g", "-f", "worstaudio/worst", f"{CHANNEL}{channel}"],
        capture_output=True,
        text=True,
        timeout=RESOLVE_S,
    )
    found = [line.strip() for line in finished.stdout.splitlines() if line.strip()]
    return found[-1] if found else ""


def _hear(stop: stream.Stop, rate: int, seconds: float) -> Iterator[np.ndarray]:
    # Resolved one at a time rather than all at once: a channel nobody reaches
    # costs nothing, and a rite that stops early has asked for nothing extra.
    playlist = resolve(stop.url)
    if not playlist:
        return iter([])
    return stream.capture(stream.Stop(stop.label, playlist, stop.number), rate, seconds)


def _stops_for(ctx, key: Key) -> list[stream.Stop]:
    channels = live(ctx, token())
    if not channels:
        raise Unavailable(
            "Twitch listed nobody broadcasting in that language. Change "
            "modules.twitch_voice.language with :set, or draw again."
        )
    random.Random(key.seed).shuffle(channels)
    return [stop for stop in map(described, channels) if stop.url]
