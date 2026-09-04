import math
import os
import random
import select
import shutil
import statistics
import subprocess
import time
from typing import Iterator

import numpy as np

from heidr import audio
from heidr.contracts import Cancelled, Unavailable
from heidr.stt.base import RATE as SPEECH_RATE

BLOCK = 4096
GRID = 200
# librtlsdr will not run the receiver below about this, and rtl_fm answers an
# input rate under it by producing nothing at all rather than complaining.
MIN_INPUT_HZ = 24_000
HEADER = 6
MARGIN_DB = 8.0
SEPARATION_HZ = 200_000


def band_edges(band: str) -> tuple[float, float]:
    """Read `88.0-108.0` as a pair of frequencies in hertz."""
    low, _, high = band.partition("-")
    return float(low) * 1e6, float(high) * 1e6


def choose_band(bands, rng: random.Random) -> str:
    """One band per sweep.

    Shortwave broadcasting is not one band but a dozen scattered ones, and which
    of them is alive depends on the hour and the ionosphere. So a module may
    name several and let the draw pick.
    """
    if isinstance(bands, str):
        return bands
    return rng.choice(list(bands)) if bands else ""


def plan(
    band: str,
    sweep: str,
    stops: int,
    rng: random.Random,
    among: list[float] | None = None,
) -> list[float]:
    """Which frequencies to visit, in which order.

    Four sweep modes, after gqrx-ghostbox by Douglas Haber (BSD-3-Clause).
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


def rtl_power_band(band: str) -> str:
    """`88.0-108.0` is how a band is written here; rtl_power wants `low:high`."""
    if "-" in band:
        low, high = band_edges(band)
        return f"{int(low)}:{int(high)}"
    return band


def scan(band: str, step: str, seconds: int, direct: bool = False, gain: str = "") -> str:
    command = ["rtl_power", "-f", f"{rtl_power_band(band)}:{step}", "-i", str(seconds), "-1"]
    if direct:
        command += ["-D"]
    if gain:
        command += ["-g", gain]
    command += ["-"]
    finished = subprocess.run(command, capture_output=True, text=True, timeout=seconds + 30)
    return finished.stdout


def read_bounded(process, size: int, deadline: float) -> bytes:
    """Whatever the pipe holds, and never a wait past the deadline.

    `read` returns only once it has a whole block or the pipe closes, so a
    source that sends a little and then goes quiet without closing blocks for
    ever and the deadline is never looked at again. `select` puts the deadline
    on the wait itself.
    """
    left = deadline - time.monotonic()
    if left <= 0:
        return b""
    ready, _, _ = select.select([process.stdout], [], [], left)
    return os.read(process.stdout.fileno(), size) if ready else b""


def blocks_from(process, size: int, deadline: float) -> Iterator[np.ndarray]:
    """Whole samples out of a pipe, bounded by the deadline."""
    remainder = b""
    while True:
        raw = read_bounded(process, size, deadline)
        if not raw:
            return
        raw = remainder + raw
        # A bounded read returns what is there, which can split a sample down
        # the middle; the buffer is read as pairs of bytes and an odd one would
        # raise. The stray byte waits for the rest of its sample.
        whole = len(raw) - len(raw) % 2
        remainder = raw[whole:]
        if whole:
            yield audio.to_float(raw[:whole])


def capture(
    frequency: float,
    mode: str,
    rate: int,
    seconds: float,
    gain: str = "",
    input_rate: str = "",
    direct: str = "",
) -> Iterator[np.ndarray]:
    """Read demodulated audio from rtl_fm one block at a time.

    `rate` is the rate the audio comes out at and goes to `-r`, not to `-s`.
    The distinction matters: rtl_fm's own help spells `wbfm` out as
    `-M fm -s 170k -o 4 -A fast -r 32k -l 0 -E deemp`, so a broadcast needs
    170 kHz of input to demodulate. Setting `-s` to the output rate narrows the
    input to 32 kHz, which throws away most of the signal and leaves hiss —
    measurably so: two and a half times more energy above 8 kHz.
    """
    command = ["rtl_fm", "-f", str(int(frequency)), "-M", mode]
    if input_rate:
        command += ["-s", input_rate]
    command += ["-r", str(rate)]
    if gain:
        command += ["-g", gain]
    if direct:
        # The tuner cannot reach below about 24 MHz, so shortwave and medium
        # wave arrive by sampling the input directly instead.
        command += ["-E", direct]
    command += ["-"]

    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0
    )
    try:
        yield from blocks_from(process, BLOCK * 2, time.monotonic() + seconds)
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
    band = choose_band(settings["band"], rng)
    ctx.emit("stage", f"band {band} MHz")
    stops = _stops_for(ctx, band, rng)
    own = output is None
    if own:
        # The levels come from the interface when there is one, so the volume
        # keys reach the sound while it is still playing.
        output = audio.Output(ctx.levels or audio.Levels.from_config(ctx.config), rate)
        if ctx.has("audio"):
            output.open()
    try:
        heard, blocks = _sweep(ctx, stops, output, rate)
    finally:
        if own:
            output.close()

    if blocks == 0:
        raise Unavailable(
            "The radio gave nothing across the whole sweep. Either another "
            "program is holding the dongle or rtl_fm cannot open it. Close the "
            "other program, then draw again."
        )
    return transcribe(ctx, heard), stops


def _sweep(ctx, stops, output, rate: int) -> tuple[list[np.ndarray], int]:
    settings = ctx.settings
    heard: list[np.ndarray] = []
    blocks = 0
    for number, frequency in enumerate(stops, start=1):
        # The sweep is the longest thing the program does, so it says how far
        # along it is; the window title is the only place that shows when the
        # window is hidden.
        ctx.emit("progress", (number, len(stops)))
        if ctx.cancelled():
            # Between stops, not after all of them: twenty seconds is a long
            # time to keep someone who has changed their mind.
            raise Cancelled
        ctx.emit("stage", f"{frequency / 1e6:.3f} MHz")
        for block in capture(
            frequency,
            settings["mode"],
            rate,
            float(settings["dwell_s"]),
            gain=str(settings.get("gain", "")),
            input_rate=str(settings.get("input_rate", "")),
            direct=str(settings.get("direct", "")),
        ):
            output.play(block)
            ctx.emit("spectrum", audio.spectrum(block, int(settings.get("bins", 64))))
            heard.append(downsample(block, rate // SPEECH_RATE))
            blocks += 1
    return heard, blocks


def _carriers(ctx, band: str) -> list[float]:
    """Scan first, so the dwell happens on transmitters rather than on air.

    Landing on empty spectrum wastes the dwell and gives the recogniser nothing
    but hiss to invent words out of. A scan costs a few seconds once and makes
    every stop a real broadcast.
    """
    settings = ctx.settings
    csv = scan(
        band,
        settings["scan_step"],
        int(settings["scan_s"]),
        direct=bool(settings.get("direct")),
        gain=str(settings.get("gain", "")),
    )
    found = stations(
        power_bins(csv),
        margin=float(settings.get("scan_margin", MARGIN_DB)),
        separation=int(settings.get("scan_separation", SEPARATION_HZ)),
    )
    ctx.emit("stage", f"scan found {len(found)} carriers")
    return [float(hertz) for hertz, _power in found]


def _stops_for(ctx, band: str, rng: random.Random) -> list[float]:
    settings = ctx.settings
    carriers = _carriers(ctx, band) if settings.get("tuned") else None
    if carriers is not None and not carriers:
        # An empty band is a real answer, but so is a scan that went wrong, and
        # from here they look the same. Fall back to the even grid and say so.
        ctx.emit("stage", "no carriers, sweeping blind")
        carriers = None
    return plan(band, settings["sweep"], int(settings["stops"]), rng, among=carriers)


def downsample(block: np.ndarray, factor: int) -> np.ndarray:
    # Averaging pairs of samples, with no anti-alias filter. Crude, but speech
    # survives it and the recogniser is the next stop, not a listener.
    if factor <= 1 or block.size < factor:
        return block
    usable = block.size - (block.size % factor)
    return block[:usable].reshape(-1, factor).mean(axis=1).astype(np.float32)


def transcribe(ctx, blocks: list[np.ndarray]) -> list[str]:
    # Nothing reaches the screen while a recogniser works, and a large model on
    # a long capture takes minutes. Saying so is the whole difference between
    # waiting and wondering whether it died.
    heard = sum(block.size for block in blocks) / SPEECH_RATE
    ctx.emit("working", f"listening back to {heard:.0f}s")
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
