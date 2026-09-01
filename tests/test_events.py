import threading

from heidr.events import Bus


def test_every_subscriber_of_an_event_is_called():
    bus = Bus()
    seen = []
    bus.subscribe("spectrum", seen.append)
    bus.subscribe("spectrum", seen.append)

    bus.emit("spectrum", [1, 2, 3])

    assert seen == [[1, 2, 3], [1, 2, 3]]


def test_events_without_subscribers_are_dropped_quietly():
    Bus().emit("nobody-listens", 1)


def test_unsubscribing_stops_delivery():
    bus = Bus()
    seen = []
    stop = bus.subscribe("token", seen.append)

    bus.emit("token", "a")
    stop()
    bus.emit("token", "b")

    assert seen == ["a"]
    assert bus.subscribers("token") == 0


def test_a_handler_may_subscribe_while_an_event_is_being_delivered():
    bus = Bus()
    seen = []

    def late(payload):
        bus.subscribe("stage", seen.append)

    bus.subscribe("stage", late)
    bus.emit("stage", "first")
    bus.emit("stage", "second")

    assert seen == ["second"]


def test_emitting_from_another_thread_reaches_the_subscriber():
    bus = Bus()
    seen = []
    bus.subscribe("audio", seen.append)

    worker = threading.Thread(target=bus.emit, args=("audio", b"pcm"))
    worker.start()
    worker.join()

    assert seen == [b"pcm"]
