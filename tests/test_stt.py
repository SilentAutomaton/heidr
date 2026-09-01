import wave

import numpy as np
import pytest

from heidr import stt
from heidr.contracts import Unavailable
from heidr.stt import api, base, vosk, whisper_cpp

SPEECH = np.sin(np.linspace(0, 200, base.RATE)).astype(np.float32)


def test_build_returns_the_configured_provider(default_config):
    default_config.set("stt.provider", "whisper_cpp")
    assert stt.build(default_config).name == "whisper_cpp"


def test_build_lists_the_choices_when_the_name_is_wrong(default_config):
    default_config.set("stt.provider", "lip-reading")

    with pytest.raises(Unavailable) as refused:
        stt.build(default_config)

    assert "vosk" in str(refused.value)


def test_floats_become_sixteen_bit_samples():
    raw = base.to_pcm(np.array([0.0, 0.5, -0.5, 2.0], dtype=np.float32))
    assert list(np.frombuffer(raw, dtype="<i2")) == [0, 16383, -16383, 32767]


def test_joining_no_blocks_gives_no_audio():
    assert base.joined([]).size == 0


# whisper.cpp


def test_whisper_needs_both_a_binary_and_a_model(default_config, tmp_path):
    default_config.set("stt.binary", "/usr/bin/whisper-cli")
    provider = whisper_cpp.WhisperCpp(default_config)
    assert provider.available() is False

    model = tmp_path / "model.bin"
    model.write_bytes(b"weights")
    default_config.set("stt.model_path", str(model))
    assert whisper_cpp.WhisperCpp(default_config).available() is True


def test_whisper_splits_long_audio_into_windows(default_config, monkeypatch):
    default_config.set("stt.window_s", 1)
    provider = whisper_cpp.WhisperCpp(default_config)
    monkeypatch.setattr(provider, "run", lambda window: f"window of {window.size}")

    said = list(provider.transcribe([SPEECH, SPEECH, SPEECH]))

    assert len(said) == 3
    assert all(partial.final for partial in said)


def test_whisper_says_nothing_about_silence(default_config, monkeypatch):
    provider = whisper_cpp.WhisperCpp(default_config)
    monkeypatch.setattr(provider, "run", lambda window: "   ")

    assert list(provider.transcribe([SPEECH])) == []


def test_the_written_window_is_a_readable_mono_wave(tmp_path):
    path = tmp_path / "window.wav"
    whisper_cpp.write_wav(path, SPEECH)

    with wave.open(str(path), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getframerate() == base.RATE
        assert handle.getnframes() == SPEECH.size


# hosted service


def test_the_api_provider_needs_a_key(default_config, monkeypatch):
    monkeypatch.delenv("HEIDR_STT_KEY", raising=False)
    assert api.Remote(default_config).available() is False

    with pytest.raises(Unavailable) as refused:
        list(api.Remote(default_config).transcribe([SPEECH]))
    assert "HEIDR_STT_KEY" in str(refused.value)


def test_the_api_provider_sends_a_wave_file_and_reads_the_text(default_config, monkeypatch):
    monkeypatch.setenv("HEIDR_STT_KEY", "secret-value")
    sent = {}

    class Reply:
        def raise_for_status(self):
            return None

        def json(self):
            return {"text": "  numbers, spoken slowly  "}

    def post(url, **kwargs):
        sent.update(kwargs)
        sent["url"] = url
        return Reply()

    monkeypatch.setattr(api, "requests", type("R", (), {"post": staticmethod(post)}))

    said = list(api.Remote(default_config).transcribe([SPEECH]))

    assert said == [base.Partial("numbers, spoken slowly", final=True)]
    assert sent["url"].endswith("/v1/audio/transcriptions")
    assert sent["files"]["file"][2] == "audio/wav"
    assert sent["headers"]["authorization"] == "Bearer secret-value"


# vosk


def test_vosk_is_unavailable_without_its_model(default_config):
    assert vosk.Vosk(default_config).available() is False


def test_vosk_reports_partials_then_a_final_line(default_config, monkeypatch, tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    default_config.set("stt.model_path", str(model))

    provider = vosk.Vosk(default_config)
    monkeypatch.setattr(provider, "_recogniser", lambda: FakeRecogniser())

    said = list(provider.transcribe([SPEECH, SPEECH]))

    assert [partial.text for partial in said] == ["one", "one two"]
    assert [partial.final for partial in said] == [False, True]


class FakeRecogniser:
    def __init__(self):
        self.calls = 0

    def AcceptWaveform(self, data):
        self.calls += 1
        return self.calls > 1

    def PartialResult(self):
        return '{"partial": "one"}'

    def Result(self):
        return '{"text": "one two"}'

    def FinalResult(self):
        return '{"text": ""}'
