import random
import shutil
import subprocess
import time
from typing import Iterator

import numpy as np

from heidr import audio
from heidr.stt.base import RATE as SPEECH_RATE

BLOCK = 4096
GRID = 200


def band_edges(band: str) -> tuple[float, float]:
    """Read `88.0-108.0` as a pair of frequencies in hertz."""
    low, _, high = band.partition("-")
    return float(low) * 1e6, float(high) * 1e6


def plan(band: str, sweep: str, stops: int, rng: random.Random) -> list[float]:
    """Which frequencies to visit, in which order.

    Four sweep modes, after gqrx-ghostbox by Doug Haber (ISC).
    https://github.com/DougHaber/gqrx-ghostbox
    """
    low, high = band_edges(band)
    stops = max(1, stops)

    if sweep == "random":
        grid = [low + (high - low) * index / (GRID - 1) for index in range(GRID)]
        return rng.sample(grid, min(stops, len(grid)))

    if sweep == "bounce":
        half = max(2, stops // 2 + stops % 2)
        up = [low + (high - low) * index / (half - 1) for index in range(half)]
        return (up + up[-2::-1])[:stops]

    step = (high - low) / max(stops - 1, 1)
    ascending = [low + step * index for index in range(stops)]
    return ascending if sweep == "forward" else ascending[::-1]


def capture(frequency: float, mode: str, rate: int, seconds: float, gain: str = "") -> Iterator[np.ndarray]:
    """Read demodulated audio from rtl_fm one block at a time."""
    command = ["rtl_fm", "-f", str(int(frequency)), "-M", mode, "-s", str(rate)]
    if gain:
        command += ["-g", gain]
    command += ["-"]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    deadline = time.monotonic() + seconds
    try:
        while time.monotonic() < deadline:
            raw = process.stdout.read(BLOCK * 2)
            if not raw:
                break
            yield audio.to_float(raw)
    finally:
        process.terminate()
        process.wait(timeout=5)


def available(ctx) -> bool:
    return ctx.has("sdr") and ctx.has("stt") and shutil.which("rtl_fm") is not None


def gather(ctx, key, output: audio.Output | None = None) -> tuple[list[str], list[float]]:
    """Sweep the band, play what is heard, and transcribe it.

    The same buffer feeds the speaker, the waterfall and the recogniser, so the
    picture on screen is the sound in the headphones is the text below it.
    """
    settings = ctx.settings
    rng = random.Random(key.seed)
    stops = plan(settings["band"], settings["sweep"], int(settings["stops"]), rng)
    rate = int(settings["rate"])
    output = output or audio.Output(audio.Levels.from_config(ctx.config), rate)

    heard: list[np.ndarray] = []
    for frequency in stops:
        ctx.emit("stage", f"{frequency / 1e6:.3f} MHz")
        for block in capture(frequency, settings["mode"], rate, float(settings["dwell_s"])):
            output.play(block)
            ctx.emit("spectrum", audio.spectrum(block, int(settings.get("bins", 64))))
            heard.append(downsample(block, rate // SPEECH_RATE))

    return transcribe(ctx, heard), stops


def downsample(block: np.ndarray, factor: int) -> np.ndarray:
    # Averaging pairs of samples, with no anti-alias filter. Crude, but speech
    # survives it and the recogniser is the next stop, not a listener.
    if factor <= 1 or block.size < factor:
        return block
    usable = block.size - (block.size % factor)
    return block[:usable].reshape(-1, factor).mean(axis=1).astype(np.float32)


def transcribe(ctx, blocks: list[np.ndarray]) -> list[str]:
    said = []
    for partial in ctx.stt.transcribe(blocks):
        if partial.final and partial.text:
            said.append(partial.text)
            ctx.emit("token", partial.text)
    return said


def matching(said: list[str], anchors: tuple[str, ...]) -> list[str]:
    """Keep the phrases that carry one of the question's words, if any do."""
    if not anchors:
        return said
    wanted = [anchor.lower() for anchor in anchors]
    hits = [phrase for phrase in said if any(word in phrase.lower() for word in wanted)]
    return hits or said
