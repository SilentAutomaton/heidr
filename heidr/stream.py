import shutil
import subprocess
import time
from dataclasses import dataclass
from typing import Callable, Iterator

import numpy as np

from heidr import audio, radio
from heidr.contracts import Cancelled, Unavailable
from heidr.stt.base import RATE as SPEECH_RATE

BLOCK = 4096
AGENT = "heidr/0.1"
# ffmpeg reads this one in microseconds. It is the bound that kills a socket a
# server opened and then stopped feeding, which a plain connect timeout misses.
READ_TIMEOUT_US = 5_000_000
# Long enough for a name lookup, a handshake and the audio itself.
CONNECT_S = 8.0


@dataclass(frozen=True)
class Stop:
    """One place to listen: what to call it, where to get it, and its number."""

    label: str
    url: str
    number: int = 0


def command(stop: Stop, rate: int, seconds: float, agent: str = AGENT) -> list[str]:
    """One ffmpeg reading one stream into the format the recogniser wants.

    There is no `-re`. A station sends a burst when a listener connects, so the
    first seconds arrive faster than real time; real time is imposed further
    along by the sound card, which blocks until it has room. Slowing ffmpeg here
    would only slow a machine with no sound card, where nobody is listening.
    """
    return [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-user_agent",
        agent,
        "-icy",
        "0",
        "-rw_timeout",
        str(READ_TIMEOUT_US),
        "-probesize",
        "32k",
        "-analyzeduration",
        "0",
        "-i",
        stop.url,
        "-t",
        str(seconds),
        # Station artwork arrives as a video stream on a surprising number of
        # them, and without this ffmpeg refuses the raw audio output.
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(rate),
        "-f",
        "s16le",
        "-",
    ]


def capture(stop: Stop, rate: int, seconds: float) -> Iterator[np.ndarray]:
    process = subprocess.Popen(
        command(stop, rate, seconds), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    deadline = time.monotonic() + seconds + CONNECT_S
    try:
        while time.monotonic() < deadline:
            raw = process.stdout.read(BLOCK * 2)
            if not raw:
                break
            yield audio.to_float(raw)
    finally:
        process.terminate()
        process.wait(timeout=5)


def available(ctx, *tools: str) -> bool:
    if not (ctx.has("net") and ctx.has("stt")):
        return False
    return all(shutil.which(tool) is not None for tool in tools)


def gather(
    ctx,
    key,
    candidates: list[Stop],
    reader: Callable[[Stop, int, float], Iterator[np.ndarray]] | None = None,
    output: audio.Output | None = None,
) -> tuple[list[str], list[Stop]]:
    """Visit the candidates until enough of them have spoken.

    A station listed as working is not always working, so the caller offers more
    stops than are wanted and the ones that give nothing are passed over.
    """
    settings = ctx.settings
    rate = int(settings["rate"])
    own = output is None
    if own:
        output = audio.Output(ctx.levels or audio.Levels.from_config(ctx.config), rate)
        if ctx.has("audio"):
            output.open()
    try:
        heard, reached = _visit(ctx, candidates, reader or capture, output, rate)
    finally:
        if own:
            output.close()

    if not reached:
        raise Unavailable(
            "None of the stations answered. The network is down, or every one "
            "of them was offline at once. Check the connection, then draw again."
        )
    return radio.matching(radio.transcribe(ctx, heard), key.anchors), reached


def _visit(ctx, candidates, reader, output, rate: int):
    """One buffer, three consumers, on the same turn of the loop.

    What the speaker plays, what the waterfall draws and what the recogniser is
    given are the same block at the same moment. Nothing is collected first and
    played afterwards, or the picture would run ahead of the sound.
    """
    settings = ctx.settings
    wanted = max(1, int(settings["stops"]))
    bins = int(settings.get("bins", 64))
    dwell = float(settings["dwell_s"])
    heard: list[np.ndarray] = []
    reached: list[Stop] = []

    for stop in candidates:
        if len(reached) >= wanted:
            break
        if ctx.cancelled():
            raise Cancelled
        ctx.emit("progress", (len(reached) + 1, wanted))
        ctx.emit("stage", stop.label)
        blocks = 0
        for block in reader(stop, rate, dwell):
            output.play(block)
            ctx.emit("spectrum", audio.spectrum(block, bins))
            heard.append(radio.downsample(block, rate // SPEECH_RATE))
            blocks += 1
        if blocks:
            reached.append(stop)
    return heard, reached
