import math
import random
import shutil
import statistics
import subprocess
import time
from typing import Iterator

import numpy as np

from heidr import audio
from heidr.contracts import Unavailable
from heidr.stt.base import RATE as SPEECH_RATE

BLOCK = 4096
GRID = 200
HEADER = 6
MARGIN_DB = 8.0
SEPARATION_HZ = 200_000


def band_edges(band: str) -> tuple[float, float]:
    """Read `88.0-108.0` as a pair of frequencies in hertz."""
    low, _, high = band.partition("-")
    return float(low) * 1e6, float(high) * 1e6


def plan(
    band: str,
    sweep: str,
    stops: int,
    rng: random.Random,
    among: list[float] | None = None,
) -> list[float]:
    """Which frequencies to visit, in which order.

    Four sweep modes, after gqrx-ghostbox by Doug Haber (ISC).
    https://github.com/DougHaber/gqrx-ghostbox

    Without `among` the band is divided evenly and the sweep walks the grid,
    landing wherever it lands. With `among` — a list of frequencies a scan found
    carriers on — the same four orders are applied to those instead.
    """
    stops = max(1, stops)
    grid = sorted(among) if among is not None else _even_grid(band, sweep, stops)
    if not grid:
        return []

    if sweep == "random":
        return rng.sample(grid, min(stops, len(grid)))

    if sweep == "bounce":
        half = max(2, stops // 2 + stops % 2)
        up = grid[:half] if among is not None else grid
        return (up + up[-2::-1])[:stops]

    ascending = grid[:stops]
    return ascending if sweep == "forward" else ascending[::-1]


def _even_grid(band: str, sweep: str, stops: int) -> list[float]:
    low, high = band_edges(band)
    count = GRID if sweep == "random" else (max(2, stops // 2 + stops % 2) if sweep == "bounce" else stops)
    return [low + (high - low) * index / max(count - 1, 1) for index in range(count)]


def power_bins(csv: str) -> list[tuple[int, float]]:
    """Every bin of an rtl_power sweep as a frequency and a power in decibels."""
    bins = []
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
            if math.isfinite(power):
                bins.append((int(low + index * step), power))
    return bins


def stations(
    bins: list[tuple[int, float]],
    margin: float = MARGIN_DB,
    separation: int = SEPARATION_HZ,
    limit: int = 20,
) -> list[tuple[int, float]]:
    """Carriers that stand above the noise floor, strongest first.

    A broadcast sits ten decibels or more above the median of the band, so the
    median is the floor and anything well above it is a transmitter. Bins closer
    together than one channel belong to the same station, and only its loudest
    bin is kept.
    """
    if not bins:
        return []
    floor = statistics.median(power for _hertz, power in bins)
    strong = sorted(
        (pair for pair in bins if pair[1] >= floor + margin), key=lambda pair: pair[1], reverse=True
    )

    found: list[tuple[int, float]] = []
    for hertz, power in strong:
        if all(abs(hertz - taken) >= separation for taken, _ in found):
            found.append((hertz, power))
        if len(found) >= limit:
            break
    return found


def scan(band: str, step: str, seconds: int) -> str:
    command = ["rtl_power", "-f", f"{band}:{step}", "-i", str(seconds), "-1", "-"]
    finished = subprocess.run(command, capture_output=True, text=True, timeout=seconds + 30)
    return finished.stdout


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
    rate = int(settings["rate"])
    stops = plan(
        settings["band"],
        settings["sweep"],
        int(settings["stops"]),
        rng,
        among=_carriers(ctx) if settings.get("tuned") else None,
    )
    output = output or audio.Output(audio.Levels.from_config(ctx.config), rate)

    heard: list[np.ndarray] = []
    blocks = 0
    for frequency in stops:
        ctx.emit("stage", f"{frequency / 1e6:.3f} MHz")
        for block in capture(frequency, settings["mode"], rate, float(settings["dwell_s"])):
            output.play(block)
            ctx.emit("spectrum", audio.spectrum(block, int(settings.get("bins", 64))))
            heard.append(downsample(block, rate // SPEECH_RATE))
            blocks += 1

    if blocks == 0:
        raise Unavailable(
            "The radio gave nothing across the whole sweep. Either another "
            "program is holding the dongle or rtl_fm cannot open it. Close the "
            "other program, then draw again."
        )
    return transcribe(ctx, heard), stops


def _carriers(ctx) -> list[float]:
    """Scan first, so the dwell happens on transmitters rather than on air.

    Landing on empty spectrum wastes the dwell and gives the recogniser nothing
    but hiss to invent words out of. A scan costs a few seconds once and makes
    every stop a real broadcast.
    """
    found = stations(
        power_bins(scan(ctx.settings["band"], ctx.settings["scan_step"], int(ctx.settings["scan_s"])))
    )
    ctx.emit("stage", f"scan found {len(found)} carriers")
    return [float(hertz) for hertz, _power in found]


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
