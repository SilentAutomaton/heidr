import io
import wave
from typing import Iterable, Iterator

import numpy as np
import requests

from heidr.contracts import Unavailable
from heidr.stt.base import RATE, Partial, joined, to_pcm


class Remote:
    """Any service that takes an audio file and returns text.

    The shape is the OpenAI transcription endpoint, which several other services
    copied, so `base_url` is usually the only thing that changes.
    """

    name = "api"

    def __init__(self, config):
        self.base_url = config.get("stt.base_url", "https://api.openai.com").rstrip("/")
        self.model = config.get("stt.model", "whisper-1")
        self.timeout = config.get("stt.timeout", 120)
        self.key_name = config.get("stt.api_key_env", "HEIDR_STT_KEY")
        self.key = config.secret("stt.api_key_env")

    def available(self) -> bool:
        return bool(self.key)

    def transcribe(self, blocks: Iterable[np.ndarray]) -> Iterator[Partial]:
        if not self.key:
            raise Unavailable(
                f"No API key for speech recognition. The {self.key_name} "
                "environment variable is empty. Export it and start again."
            )
        audio = joined(blocks)
        if audio.size == 0:
            return

        reply = requests.post(
            f"{self.base_url}/v1/audio/transcriptions",
            headers={"authorization": f"Bearer {self.key}"},
            files={"file": ("window.wav", wav_bytes(audio), "audio/wav")},
            data={"model": self.model},
            timeout=self.timeout,
        )
        reply.raise_for_status()
        text = reply.json().get("text", "").strip()
        if text:
            yield Partial(text, final=True)


def wav_bytes(audio: np.ndarray) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(RATE)
        handle.writeframes(to_pcm(audio))
    return buffer.getvalue()
