import shutil
import subprocess
import tempfile
import wave
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np

from heidr.stt.base import RATE, Partial, joined, to_pcm

BINARIES = ("whisper-cli", "whisper-cpp", "main")


class WhisperCpp:
    """A window of audio at a time through the whisper.cpp binary.

    Not streaming: whisper works on a whole window, so nothing appears until the
    window closes. In exchange it hears far more of a noisy shortwave broadcast
    than a streaming recogniser does.
    """

    name = "whisper_cpp"

    def __init__(self, config):
        self.binary = config.get("stt.binary", "") or self._find()
        self.model = config.get("stt.model_path", "")
        self.language = config.get("stt.language", "auto")
        self.threads = int(config.get("stt.threads", 0)) or None
        self.window_s = int(config.get("stt.window_s", 30))

    def _find(self) -> str:
        for candidate in BINARIES:
            found = shutil.which(candidate)
            if found:
                return found
        return ""

    def available(self) -> bool:
        return bool(self.binary) and bool(self.model) and Path(self.model).is_file()

    def transcribe(self, blocks: Iterable[np.ndarray]) -> Iterator[Partial]:
        audio = joined(blocks)
        if audio.size == 0:
            return
        for window in self._windows(audio):
            text = self.run(window).strip()
            if text:
                yield Partial(text, final=True)

    def _windows(self, audio: np.ndarray) -> Iterator[np.ndarray]:
        size = self.window_s * RATE
        for start in range(0, audio.size, size):
            yield audio[start : start + size]

    def run(self, audio: np.ndarray) -> str:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "window.wav"
            write_wav(path, audio)
            command = [self.binary, "-m", self.model, "-f", str(path), "-nt", "-l", self.language]
            if self.threads:
                command += ["-t", str(self.threads)]
            finished = subprocess.run(command, capture_output=True, text=True)
        return " ".join(finished.stdout.split())


def write_wav(path: Path, audio: np.ndarray) -> None:
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(to_pcm(audio))
