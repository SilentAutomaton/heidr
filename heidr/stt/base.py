from dataclasses import dataclass
from typing import Iterable, Iterator, Protocol

import numpy as np

from heidr.contracts import Unavailable

RATE = 16000


@dataclass(frozen=True)
class Partial:
    text: str
    final: bool


class Speech(Protocol):
    name: str

    def available(self) -> bool: ...

    def transcribe(self, blocks: Iterable[np.ndarray]) -> Iterator[Partial]: ...


def build(config) -> Speech:
    from heidr.stt import api, vosk, whisper_cpp

    makers = {
        "vosk": vosk.Vosk,
        "whisper_cpp": whisper_cpp.WhisperCpp,
        "api": api.Remote,
    }
    chosen = config.get("stt.provider", "")
    if chosen not in makers:
        raise Unavailable(
            f"No speech provider named {chosen!r}. "
            f"Set stt.provider to one of: {', '.join(sorted(makers))}."
        )
    return makers[chosen](config)


def to_pcm(block: np.ndarray) -> bytes:
    return (np.clip(block, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def joined(blocks: Iterable[np.ndarray]) -> np.ndarray:
    parts = list(blocks)
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
