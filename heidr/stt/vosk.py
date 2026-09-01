import json
from pathlib import Path
from typing import Iterable, Iterator

import numpy as np

from heidr.stt.base import RATE, Partial, to_pcm


class Vosk:
    """Genuinely streaming: partial words appear while the speaker is talking.

    Less accurate than whisper on noisy radio, but it answers as it goes, which
    is what dictating a question wants.
    """

    name = "vosk"

    def __init__(self, config):
        self.model_path = config.get("stt.model_path", "")

    def available(self) -> bool:
        if not self.model_path or not Path(self.model_path).expanduser().is_dir():
            return False
        try:
            import vosk  # noqa: F401
        except Exception:
            return False
        return True

    def _recogniser(self):
        import vosk

        vosk.SetLogLevel(-1)
        return vosk.KaldiRecognizer(vosk.Model(str(Path(self.model_path).expanduser())), RATE)

    def transcribe(self, blocks: Iterable[np.ndarray]) -> Iterator[Partial]:
        recogniser = self._recogniser()
        for block in blocks:
            if recogniser.AcceptWaveform(to_pcm(block)):
                said = json.loads(recogniser.Result()).get("text", "").strip()
                if said:
                    yield Partial(said, final=True)
            else:
                said = json.loads(recogniser.PartialResult()).get("partial", "").strip()
                if said:
                    yield Partial(said, final=False)

        last = json.loads(recogniser.FinalResult()).get("text", "").strip()
        if last:
            yield Partial(last, final=True)
