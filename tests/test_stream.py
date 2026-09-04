import subprocess
import sys
import time

import numpy as np
import pytest

from heidr import audio, net, radio, registry, stream
from heidr.contracts import Cancelled, Key, Unavailable
from heidr.stt.base import Partial
from heidr.world import kiwi_voice, net_voice, twitch_voice

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

    monkeypatch.setattr(net_voice.net, "fetch_json", lambda url, headers=None: asked.append(url) or [])

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


# kiwi_voice


KIWI_LIST = """\
// KiwiSDR.com receiver list for dyatlov map maker
var kiwisdr_com =
[
\t{
\t\t"status":"active", "offline":"no", "url":"http://one.example:8073",
\t\t"loc":"Tarlee", "bands":"1800000-30000000", "users":"3", "users_max":"8",
\t},
\t{
\t\t"status":"active", "offline":"no", "url":"http://full.example:8074",
\t\t"loc":"Boras", "bands":"0-30000000", "users":"8", "users_max":"8",
\t},
\t{
\t\t"status":"active", "offline":"no", "url":"http://vhf.example:8073",
\t\t"loc":"Nowhere", "bands":"144000000-146000000", "users":"0", "users_max":"4",
\t},
\t{
\t\t"status":"inactive", "offline":"yes", "url":"http://gone.example:8073",
\t\t"loc":"Gone", "bands":"0-30000000", "users":"0", "users_max":"8",
\t},
]
"""


def test_the_receiver_list_is_javascript_not_json():
    listed = kiwi_voice.receivers(KIWI_LIST)

    assert len(listed) == 4
    assert listed[0]["loc"] == "Tarlee"


def test_a_list_that_is_not_a_list_at_all_is_no_receivers():
    assert kiwi_voice.receivers("nothing here") == []
    assert kiwi_voice.receivers("var x = [ broken ]") == []


def test_only_a_free_receiver_that_reaches_the_band_is_used():
    listed = kiwi_voice.receivers(KIWI_LIST)
    free = [entry for entry in listed if kiwi_voice.listening(entry, 9_500_000)]

    assert [entry["loc"] for entry in free] == ["Tarlee"]


def test_a_receiver_with_no_free_slot_is_left_alone():
    full = {"status": "active", "offline": "no", "url": "http://a", "bands": "0-30000000",
            "users": "8", "users_max": "8"}

    assert kiwi_voice.listening(full, 9_500_000) is False


def test_the_recorder_is_told_the_frequency_in_kilohertz():
    stop = kiwi_voice.described({"url": "http://one.example:8073", "loc": "Tarlee"}, 9_500_000)

    assert stop.number == 9500
    assert stop.label == "9.500 MHz via Tarlee"
    assert kiwi_voice._address(stop.url) == ("one.example", 8073)


def test_a_receiver_url_without_a_port_gets_the_usual_one():
    assert kiwi_voice._address("one.example") == ("one.example", 8073)


def test_no_free_receiver_says_whose_radios_these_are(stub_context, monkeypatch):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "kiwi_voice")
    monkeypatch.setattr(kiwi_voice.net, "fetch_text", lambda url, headers=None: "")

    with pytest.raises(Unavailable) as refused:
        kiwi_voice._stops_for(scoped, Key(seed=1))

    assert "other people's" in str(refused.value)


def test_every_stop_is_on_a_different_receiver(stub_context, monkeypatch):
    ctx = listening(stub_context)
    _found, scoped = ready(ctx, "kiwi_voice")
    monkeypatch.setattr(kiwi_voice.net, "fetch_text", lambda url, headers=None: KIWI_LIST)

    stops = kiwi_voice._stops_for(scoped, Key(seed=4))

    assert len({stop.url for stop in stops}) == len(stops)


def test_kiwi_voice_reports_the_receivers_it_reached(stub_context, monkeypatch):
    ctx = listening(stub_context, ["heard on shortwave"])
    found, scoped = ready(ctx, "kiwi_voice")
    scoped.stt = ctx.stt
    scoped.settings["stops"] = 1
    monkeypatch.setattr(kiwi_voice.net, "fetch_text", lambda url, headers=None: KIWI_LIST)
    monkeypatch.setattr(kiwi_voice, "capture", lambda stop, rate, seconds, binary: iter([tone()]))
    monkeypatch.setattr(audio, "Output", lambda levels, rate: FakeOutput([]))

    material = found.run(scoped, Key(seed=2))

    assert material.text == "heard on shortwave"
    assert material.source == "kiwisdr"
    assert len(material.extra["receivers"]) == 1


def test_kiwi_voice_needs_the_recorder_on_the_path(stub_context, monkeypatch):
    module = registry.MODULES["world"]["kiwi_voice"]
    online = stub_context.with_capabilities("net", "stt")

    monkeypatch.setattr(stream.shutil, "which", lambda name: None)
    assert module.available(online) is False

    monkeypatch.setattr(stream.shutil, "which", lambda name: f"/usr/bin/{name}")
    assert module.available(online) is True
    assert module.available(stub_context) is False


# twitch_voice


CHANNELS = {
    "data": [
        {"user_name": "Somebody", "user_login": "somebody", "viewer_count": 412},
        {"user_name": "Another", "user_login": "another", "viewer_count": 37},
        {"user_name": "", "user_login": "", "viewer_count": 0},
    ]
}


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv(twitch_voice.ID_ENV, "an-id")
    monkeypatch.setenv(twitch_voice.SECRET_ENV, "a-secret")


def test_the_credentials_reach_both_twitch_endpoints(stub_context, keyed, monkeypatch):
    _found, scoped = ready(stub_context.with_capabilities("net", "stt"), "twitch_voice")
    asked = {}

    monkeypatch.setattr(
        twitch_voice.net, "post_json", lambda url, payload: {"access_token": "bearer-value"}
    )

    def fetch(url, headers=None):
        asked["url"], asked["headers"] = url, headers
        return CHANNELS

    monkeypatch.setattr(twitch_voice.net, "fetch_json", fetch)

    twitch_voice.live(scoped, twitch_voice.token())

    assert asked["headers"] == {"Client-Id": "an-id", "Authorization": "Bearer bearer-value"}
    assert "type=live" in asked["url"] and "language=en" in asked["url"]


def test_a_refused_token_names_the_variables_to_check(keyed, monkeypatch):
    monkeypatch.setattr(twitch_voice.net, "post_json", lambda url, payload: {})

    with pytest.raises(Unavailable) as refused:
        twitch_voice.token()

    assert twitch_voice.ID_ENV in str(refused.value)
    assert twitch_voice.SECRET_ENV in str(refused.value)


def test_a_channel_becomes_a_stop_named_by_its_broadcaster():
    stop = twitch_voice.described(CHANNELS["data"][0])

    assert stop.label == "Somebody"
    assert stop.url == "somebody"
    assert stop.number == 412


def test_a_channel_with_no_name_is_dropped(stub_context, keyed, monkeypatch):
    _found, scoped = ready(stub_context.with_capabilities("net", "stt"), "twitch_voice")
    monkeypatch.setattr(twitch_voice, "token", lambda: "bearer-value")
    monkeypatch.setattr(twitch_voice, "live", lambda ctx, bearer: list(CHANNELS["data"]))

    stops = twitch_voice._stops_for(scoped, Key(seed=1))

    assert [stop.url for stop in stops] == ["another", "somebody"]


def test_nobody_broadcasting_says_which_setting_to_change(stub_context, keyed, monkeypatch):
    _found, scoped = ready(stub_context.with_capabilities("net", "stt"), "twitch_voice")
    monkeypatch.setattr(twitch_voice, "token", lambda: "bearer-value")
    monkeypatch.setattr(twitch_voice, "live", lambda ctx, bearer: [])

    with pytest.raises(Unavailable) as refused:
        twitch_voice._stops_for(scoped, Key(seed=1))

    assert "language" in str(refused.value)


def test_a_channel_is_resolved_only_when_it_is_reached(stub_context, keyed, monkeypatch):
    ctx = listening(stub_context, ["said on a stream"])
    found, scoped = ready(ctx, "twitch_voice")
    scoped.stt = ctx.stt
    scoped.settings["stops"] = 1
    resolved = []

    monkeypatch.setattr(twitch_voice, "token", lambda: "bearer-value")
    monkeypatch.setattr(twitch_voice, "live", lambda ctx, bearer: list(CHANNELS["data"][:2]))
    monkeypatch.setattr(
        twitch_voice, "resolve", lambda channel: resolved.append(channel) or "http://hls/live.m3u8"
    )
    monkeypatch.setattr(stream, "capture", lambda stop, rate, seconds: iter([tone()]))
    monkeypatch.setattr(audio, "Output", lambda levels, rate: FakeOutput([]))

    material = found.run(scoped, Key(seed=1))

    assert material.text == "said on a stream"
    assert material.source == "twitch"
    # One stop wanted, so only one channel was ever asked about.
    assert len(resolved) == 1


def test_a_channel_that_went_dark_is_passed_over(monkeypatch):
    monkeypatch.setattr(twitch_voice, "resolve", lambda channel: "")

    assert list(twitch_voice._hear(stream.Stop("gone", "gone"), 16000, 5)) == []


def test_the_resolver_takes_the_last_url_it_printed(monkeypatch):
    class Finished:
        stdout = "\nhttp://first/only-video\nhttp://second/audio.m3u8\n"

    monkeypatch.setattr(twitch_voice.subprocess, "run", lambda *args, **kwargs: Finished())

    assert twitch_voice.resolve("somebody") == "http://second/audio.m3u8"


def test_twitch_voice_stays_out_of_the_lottery_without_credentials(stub_context, monkeypatch):
    module = registry.MODULES["world"]["twitch_voice"]
    online = stub_context.with_capabilities("net", "stt")
    monkeypatch.setattr(stream.shutil, "which", lambda name: f"/usr/bin/{name}")

    monkeypatch.delenv(twitch_voice.ID_ENV, raising=False)
    monkeypatch.delenv(twitch_voice.SECRET_ENV, raising=False)
    assert module.available(online) is False

    monkeypatch.setenv(twitch_voice.ID_ENV, "an-id")
    assert module.available(online) is False

    monkeypatch.setenv(twitch_voice.SECRET_ENV, "a-secret")
    assert module.available(online) is True

    monkeypatch.setattr(stream.shutil, "which", lambda name: None)
    assert module.available(online) is False


# A source that goes quiet


# One partial block, then silence, and the pipe never closes. This is what a
# public receiver does when it stops answering, and it used to hang the run for
# as long as anybody was willing to wait.
QUIET = "import sys, time; sys.stdout.buffer.write(b'\\0' * 4096); sys.stdout.flush(); time.sleep(600)"


def quiet_process():
    return subprocess.Popen([sys.executable, "-c", QUIET], stdout=subprocess.PIPE, bufsize=0)


def test_a_source_that_goes_quiet_does_not_hold_the_run():
    process = quiet_process()
    started = time.monotonic()
    try:
        blocks = list(radio.blocks_from(process, 8192, started + 1.0))
    finally:
        process.terminate()
        process.wait(timeout=5)

    # The half block it did send is kept; the wait for the rest is not endless.
    assert sum(block.size for block in blocks) == 2048
    assert time.monotonic() - started < 5


def test_a_sample_split_across_two_reads_is_put_back_together():
    """A bounded read returns what is there, which can be an odd number of bytes."""
    odd = "import sys, time; w = sys.stdout.buffer.write; w(b'\\1' * 3); sys.stdout.flush(); time.sleep(0.2); w(b'\\1' * 3); sys.stdout.flush()"
    process = subprocess.Popen([sys.executable, "-c", odd], stdout=subprocess.PIPE, bufsize=0)
    try:
        blocks = list(radio.blocks_from(process, 8192, time.monotonic() + 3.0))
    finally:
        process.terminate()
        process.wait(timeout=5)

    # Six bytes in, three whole samples out, and nothing raised on the odd one.
    assert sum(block.size for block in blocks) == 3


def test_nothing_at_all_is_not_an_error():
    process = subprocess.Popen([sys.executable, "-c", "pass"], stdout=subprocess.PIPE, bufsize=0)
    try:
        assert list(radio.blocks_from(process, 8192, time.monotonic() + 2.0)) == []
    finally:
        process.wait(timeout=5)
