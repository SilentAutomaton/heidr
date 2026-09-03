import time

import pytest
import requests

from heidr import net
from heidr.contracts import Unavailable


def test_a_reply_comes_back_decoded(monkeypatch):
    monkeypatch.setattr(net, "_get", lambda url, timeout, agent="": {"ok": True})

    assert net.fetch_json("https://example.org/feed") == {"ok": True}


def test_a_slow_source_is_abandoned_within_the_budget(monkeypatch):
    def slow(url, timeout, agent=""):
        time.sleep(5)
        return {"too": "late"}

    monkeypatch.setattr(net, "_get", slow)
    started = time.monotonic()

    with pytest.raises(Unavailable) as refused:
        net.fetch_json("https://earthquake.usgs.gov/feed", budget=0.4)

    assert time.monotonic() - started < 3
    assert "earthquake.usgs.gov" in str(refused.value)
    assert "did not answer" in str(refused.value)


def test_a_refused_connection_says_what_to_check(monkeypatch):
    def broken(url, timeout, agent=""):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr(net, "_get", broken)

    with pytest.raises(Unavailable) as refused:
        net.fetch_json("https://blockchain.info/latestblock")

    assert "Check the network" in str(refused.value)


def test_the_host_is_named_even_for_an_odd_url():
    assert net._host("https://api.adsb.lol/v2") == "api.adsb.lol"
    assert net._host("not-a-url") == "not-a-url"
