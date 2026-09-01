from typing import Callable, Iterator

import numpy as np

from heidr.stt.base import RATE

BLOCK = 4000


def available(ctx) -> bool:
    if ctx.stt is None:
        return False
    try:
        import sounddevice  # noqa: F401
    except Exception:
        return False
    return True


def record(seconds: float, rate: int = RATE) -> Iterator[np.ndarray]:
    """Blocks from the microphone, and only ever for this."""
    import sounddevice

    with sounddevice.InputStream(samplerate=rate, channels=1, dtype="float32") as stream:
        for _ in range(int(seconds * rate / BLOCK)):
            block, _overflowed = stream.read(BLOCK)
            yield block.reshape(-1)


def dictate(ctx, on_partial: Callable[[str], None], seconds: float = 15.0) -> str:
    """Speak a question instead of typing it.

    The microphone is used here and nowhere else in the program.
    """
    said: list[str] = []
    for partial in ctx.stt.transcribe(record(seconds)):
        if partial.final:
            said.append(partial.text)
            on_partial(" ".join(said))
        else:
            on_partial(" ".join(said + [partial.text]))
    return " ".join(said).strip()
