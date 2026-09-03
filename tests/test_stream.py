import numpy as np
import pytest

from heidr import audio, net, registry, stream
from heidr.contracts import Cancelled, Key, Unavailable
from heidr.stt.base import Partial
from heidr.world import net_voice

STATIONS = [
    {"name": "Raadio 2", "country": "Estonia", "bitrate": 128, "url": "http://a/1", "url_resolved": "http://a/1.mp3"},
    {"name": "Okerwelle", "country": "Germany", "bitrate": 192, "url": "http://b/2", "url_resolved": "http://b/2.mp3"},
    {"name": "no url at all", "country": "", "bitrate": 0, "url": "", "url_resolved": ""},
]


class FakeSpeech:
    name = "fake"

    def __init__(self, phrases):
        self.phrases = phrases
        self.blocks = 0

    def available(self):
        return True

    def transcribe(self, blocks):
        self.blocks = len(list(blocks))
        for phrase in self.phrases:
            yield Partial(phrase, final=True)


class FakeOutput:
    """A speaker that only remembers what reached it, and when."""

    def __init__(self, log):
        self.log = log
        self.opened = 0
        self.closed = 0

    def open(self):
        self.opened += 1
        self.log.append("open")
        return True

    def play(self, block):
        self.log.append("play")
        return block

    def close(self):
        self.closed += 1
        self.log.append("close")


def ready(ctx, name: str):
    found = registry.MODULES["world"][name]
    return found, ctx.for_module(name, found.defaults)


def listening(ctx, phrases=("a voice from the net",)):
    ctx = ctx.with_capabilities("net", "stt")
    ctx.stt = FakeSpeech(list(phrases))
    return ctx


def tone(size: int = 4096) -> np.ndarray:
    return np.sin(np.linspace(0, 50, size)).astype(np.float32)


# The ffmpeg command line


def test_the_capture_asks_for_what_the_recogniser_wants():
    argv = stream.command(stream.Stop("a station", "http://host/live.mp3"), 16000, 5)

    assert argv[:1] == ["ffmpeg"]
    assert argv[-7:] == ["-ac", "1", "-ar", "16000", "-f", "s16le", "-"]
    assert "-vn" in argv
    assert argv[argv.index("-i") + 1] == "http://host/live.mp3"
    assert argv[argv.index("-t") + 1] == "5"


def test_the_capture_is_bounded_at_the_socket():
    argv = stream.command(stream.Stop("a station", "http://host/live.mp3"), 16000, 5)

    assert argv[argv.index("-rw_timeout") + 1] == str(stream.READ_TIMEOUT_US)
    assert argv[argv.index("-user_agent") + 1] == stream.AGENT


def test_the_stream_is_never_slowed_to_real_time():
    # Real time comes from the sound card. A machine with no card must stay
    # fast, and the burst a station sends on connect must not be thrown away.
    assert "-re" not in stream.command(stream.Stop("a", "http://b"), 16000, 5)


# One buffer, three consumers


def test_every_block_reaches_the_speaker_the_screen_and_the_recogniser(stub_context, events):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt
    log: list[str] = []
    speaker = FakeOutput(log)

    def reader(stop, rate, seconds):
        for _ in range(3):
            log.append("read")
            yield tone()

    said, reached = stream.gather(
        scoped, Key(seed=1), [stream.Stop("one", "http://a")], reader=reader, output=speaker
    )

    assert said == ["a voice from the net"]
    assert len(reached) == 1
    # Read, play, read, play: nothing is collected first and played afterwards.
    assert log == ["read", "play", "read", "play", "read", "play"]
    assert [name for name, _ in events].count("spectrum") == 3
    assert ctx.stt.blocks == 3


def test_the_speaker_is_opened_once_for_the_whole_visit(stub_context):
    ctx = listening(stub_context).with_capabilities("audio")
    _found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt
    scoped.settings["stops"] = 2
    log: list[str] = []
    speaker = FakeOutput(log)

    stream.gather(
        scoped,
        Key(seed=1),
        [stream.Stop("one", "http://a"), stream.Stop("two", "http://b")],
        reader=lambda stop, rate, seconds: iter([tone()]),
        output=speaker,
    )

    # The caller owns the speaker here, so gather neither opens nor closes it.
    assert speaker.opened == 0 and speaker.closed == 0
    assert log == ["play", "play"]


def test_a_station_that_gives_nothing_is_passed_over(stub_context):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt
    scoped.settings["stops"] = 1
    visited = []

    def reader(stop, rate, seconds):
        visited.append(stop.label)
        return iter([]) if stop.label == "dead" else iter([tone()])

    _said, reached = stream.gather(
        scoped,
        Key(seed=1),
        [stream.Stop("dead", "http://a"), stream.Stop("alive", "http://b")],
        reader=reader,
        output=FakeOutput([]),
    )

    assert visited == ["dead", "alive"]
    assert [stop.label for stop in reached] == ["alive"]


def test_no_station_answering_at_all_says_why(stub_context):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt

    with pytest.raises(Unavailable) as refused:
        stream.gather(
            scoped,
            Key(seed=1),
            [stream.Stop("dead", "http://a")],
            reader=lambda stop, rate, seconds: iter([]),
            output=FakeOutput([]),
        )

    assert "None of the stations answered" in str(refused.value)


def test_a_reader_who_changed_their_mind_stops_between_stations(stub_context):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt
    scoped.cancelled = lambda: True

    with pytest.raises(Cancelled):
        stream.gather(
            scoped,
            Key(seed=1),
            [stream.Stop("one", "http://a")],
            reader=lambda stop, rate, seconds: iter([tone()]),
            output=FakeOutput([]),
        )


def test_only_as_many_stations_as_were_asked_for(stub_context):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt
    scoped.settings["stops"] = 2
    offered = [stream.Stop(str(number), f"http://{number}") for number in range(6)]

    _said, reached = stream.gather(
        scoped,
        Key(seed=1),
        offered,
        reader=lambda stop, rate, seconds: iter([tone()]),
        output=FakeOutput([]),
    )

    assert len(reached) == 2


# The directory


def test_stations_without_a_stream_are_dropped(stub_context, fake_get):
    fake_get(net, {"radio-browser.info": STATIONS})
    _found, scoped = ready(stub_context.with_capabilities("net", "stt"), "net_voice")

    assert len(net_voice.stations(scoped)) == 2


def test_the_resolved_url_is_preferred_over_the_advertised_one():
    stop = net_voice.described(STATIONS[0])

    assert stop.url == "http://a/1.mp3"
    assert stop.label == "Raadio 2 (Estonia)"
    assert stop.number == 128


def test_a_station_with_no_country_is_named_by_itself():
    assert net_voice.described({"name": "Somewhere", "url": "http://c"}).label == "Somewhere"


def test_the_filters_reach_the_directory(stub_context, monkeypatch):
    _found, scoped = ready(stub_context.with_capabilities("net", "stt"), "net_voice")
    scoped.settings["tag"] = "news"
    scoped.settings["language"] = "english"
    asked = []

    monkeypatch.setattr(net_voice.net, "fetch_json", lambda url, agent="": asked.append(url) or [])

    net_voice.stations(scoped)

    assert "hidebroken=true" in asked[0] and "order=random" in asked[0]
    assert "tag=news" in asked[0] and "language=english" in asked[0]
    assert "bitrate_min=64" in asked[0] and "codec=MP3" in asked[0]


def test_an_empty_directory_says_so(stub_context, monkeypatch):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    monkeypatch.setattr(net_voice, "stations", lambda ctx: [])

    with pytest.raises(Unavailable) as refused:
        registry.MODULES["world"]["net_voice"].run(scoped, Key(seed=1))

    assert "listed nothing" in str(refused.value)


def test_the_same_question_takes_the_same_route(stub_context, monkeypatch):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "net_voice")
    monkeypatch.setattr(net_voice, "stations", lambda ctx: list(STATIONS[:2]))

    first = [stop.label for stop in net_voice._stops_for(scoped, Key(seed=7))]
    again = [stop.label for stop in net_voice._stops_for(scoped, Key(seed=7))]

    assert first == again


def test_net_voice_reports_the_stations_it_reached(stub_context, monkeypatch):
    ctx = listening(stub_context, ["one thing said", "another"])
    found, scoped = ready(ctx, "net_voice")
    scoped.stt = ctx.stt
    scoped.settings["stops"] = 1
    monkeypatch.setattr(net_voice, "stations", lambda ctx: list(STATIONS[:1]))
    monkeypatch.setattr(stream, "capture", lambda stop, rate, seconds: iter([tone()]))
    monkeypatch.setattr(audio, "Output", lambda levels, rate: FakeOutput([]))

    material = found.run(scoped, Key(seed=1))

    assert material.text == "one thing said / another"
    assert material.source == "internet radio"
    assert material.extra["stations"] == ["Raadio 2 (Estonia)"]
    assert material.numbers == (128,)


# Availability


def test_net_voice_needs_a_network_a_recogniser_and_ffmpeg(stub_context, monkeypatch):
    module = registry.MODULES["world"]["net_voice"]

    assert module.available(stub_context) is False
    assert module.available(stub_context.with_capabilities("net")) is False
    assert module.available(stub_context.with_capabilities("stt")) is False

    monkeypatch.setattr(stream.shutil, "which", lambda name: None)
    assert module.available(stub_context.with_capabilities("net", "stt")) is False

    monkeypatch.setattr(stream.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert module.available(stub_context.with_capabilities("net", "stt")) is True
