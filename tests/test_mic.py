import numpy as np
import pytest

from heidr import mic
from heidr.stt.base import Partial


class FakeSpeech:
    def __init__(self, partials):
        self.partials = partials
        self.heard = 0

    def available(self):
        return True

    def transcribe(self, blocks):
        self.heard = len(list(blocks))
        return iter(self.partials)


def test_the_microphone_is_unavailable_without_a_speech_provider(stub_context):
    assert mic.available(stub_context) is False


def test_dictation_returns_only_the_final_words(stub_context, monkeypatch):
    stub_context.stt = FakeSpeech(
        [Partial("should", False), Partial("should the", False), Partial("should the antenna", True)]
    )
    monkeypatch.setattr(mic, "record", lambda seconds, rate=16000: iter([np.zeros(10)]))

    shown = []
    said = mic.dictate(stub_context, shown.append)

    assert said == "should the antenna"
    assert shown[0] == "should"
    assert shown[-1] == "should the antenna"


def test_saying_nothing_gives_an_empty_question(stub_context, monkeypatch):
    stub_context.stt = FakeSpeech([])
    monkeypatch.setattr(mic, "record", lambda seconds, rate=16000: iter([]))

    assert mic.dictate(stub_context, lambda said: None) == ""
