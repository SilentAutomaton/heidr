from dataclasses import dataclass

import numpy as np

FULL_SCALE = 32768.0
FLOOR = 1e-6


@dataclass
class Levels:
    target_rms: float = 0.12
    ceiling: float = 0.95
    attack_ms: int = 50
    release_ms: int = 400
    volume: float = 0.6
    muted: bool = False

    @classmethod
    def from_config(cls, config) -> "Levels":
        return cls(
            target_rms=float(config.get("audio.target_rms", 0.12)),
            ceiling=float(config.get("audio.limiter_ceiling", 0.95)),
            attack_ms=int(config.get("audio.attack_ms", 50)),
            release_ms=int(config.get("audio.release_ms", 400)),
            volume=float(config.get("audio.volume", 0.6)),
        )

    def louder(self, step: float = 0.05) -> None:
        self.volume = min(1.0, round(self.volume + step, 3))

    def quieter(self, step: float = 0.05) -> None:
        self.volume = max(0.0, round(self.volume - step, 3))


def to_float(raw: bytes) -> np.ndarray:
    return np.frombuffer(raw, dtype="<i2").astype(np.float32) / FULL_SCALE


def smoothing(milliseconds: int, samplerate: int, block: int) -> float:
    """How much of the old gain to keep for one block of this length."""
    seconds = max(milliseconds, 1) / 1000
    return float(np.exp(-(block / samplerate) / seconds))


class Gain:
    """Slow automatic gain toward a target level, then a hard ceiling.

    Every sound the program makes goes through one of these, which is why
    levelling is a property of the wiring rather than a rule to remember.
    """

    def __init__(self, levels: Levels, samplerate: int = 32000):
        self.levels = levels
        self.samplerate = samplerate
        self.gain = 1.0

    def process(self, block: np.ndarray) -> np.ndarray:
        if self.levels.muted or block.size == 0:
            return np.zeros_like(block)

        self._follow(block)
        out = block * self.gain * self.levels.volume
        return self._limit(out)

    def _follow(self, block: np.ndarray) -> None:
        rms = float(np.sqrt(np.mean(np.square(block))))
        wanted = self.levels.target_rms / max(rms, FLOOR)
        # Rising signal is caught quickly; falling signal is released slowly, so
        # a pause between words does not pump the gain up into the noise.
        milliseconds = self.levels.attack_ms if wanted < self.gain else self.levels.release_ms
        keep = smoothing(milliseconds, self.samplerate, block.size)
        self.gain = keep * self.gain + (1 - keep) * wanted

    def _limit(self, block: np.ndarray) -> np.ndarray:
        peak = float(np.max(np.abs(block))) if block.size else 0.0
        if peak > self.levels.ceiling:
            block = block * (self.levels.ceiling / peak)
        return block


def spectrum(block: np.ndarray, bins: int) -> list[float]:
    """Fold a block into `bins` bars between zero and one, ready to draw."""
    if block.size == 0 or bins <= 0:
        return [0.0] * max(bins, 0)

    magnitude = np.abs(np.fft.rfft(block * np.hanning(block.size)))
    decibels = 20 * np.log10(np.maximum(magnitude, FLOOR))
    grouped = np.array_split(decibels, bins)
    bars = np.array([part.mean() for part in grouped])

    low, high = bars.min(), bars.max()
    if high - low < FLOOR:
        return [0.0] * bins
    return ((bars - low) / (high - low)).tolist()


class Output:
    """The one place audio leaves the program."""

    def __init__(self, levels: Levels, samplerate: int = 32000):
        self.gain = Gain(levels, samplerate)
        self.samplerate = samplerate
        self.stream = None

    def open(self) -> bool:
        try:
            import sounddevice
        except Exception:
            return False
        self.stream = sounddevice.OutputStream(
            samplerate=self.samplerate, channels=1, dtype="float32"
        )
        self.stream.start()
        return True

    def play(self, block: np.ndarray) -> np.ndarray:
        levelled = self.gain.process(block)
        if self.stream is not None:
            self.stream.write(levelled.reshape(-1, 1))
        return levelled

    def close(self) -> None:
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
