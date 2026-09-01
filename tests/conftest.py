import copy

import pytest
import requests

from heidr import config, registry
from heidr.contracts import Context

registry.discover()


@pytest.fixture
def config_dirs(tmp_path):
    system = tmp_path / "etc"
    user = tmp_path / "user"
    system.mkdir()
    user.mkdir()
    return system, user


@pytest.fixture
def write_config():
    def write(directory, body: str):
        (directory / "config.toml").write_text(body)

    return write


@pytest.fixture
def default_config(tmp_path):
    settings = config.Config(config.merge(config.DEFAULTS, {}), tmp_path / "config.toml")
    settings.set("ledger.path", str(tmp_path / "ledger"))
    return settings


@pytest.fixture
def events():
    return []


@pytest.fixture
def stub_context(default_config, events):
    return Context(config=default_config, emit=lambda name, payload: events.append((name, payload)))


@pytest.fixture
def temporary_slot():
    """Give the test an empty registry, and put the real one back afterwards."""
    modules = copy.deepcopy(registry.MODULES)
    visuals = copy.deepcopy(registry.VISUALS)
    for slot in registry.MODULES:
        registry.MODULES[slot] = {}
    registry.VISUALS.clear()
    yield
    registry.MODULES.clear()
    registry.MODULES.update(modules)
    registry.VISUALS.clear()
    registry.VISUALS.update(visuals)


@pytest.fixture
def fixture_json():
    import json
    from pathlib import Path

    root = Path(__file__).parent / "fixtures"

    def read(name: str):
        return json.loads((root / f"{name}.json").read_text())

    return read


@pytest.fixture
def fake_get(monkeypatch):
    """Answer every requests.get from a table of url fragments to payloads."""

    def install(module, table: dict):
        class Reply:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        def get(url, **kwargs):
            for fragment, payload in table.items():
                if fragment in url:
                    return Reply(payload)
            raise AssertionError(f"no fixture for {url}")

        stub = type(
            "R", (), {"get": staticmethod(get), "RequestException": requests.RequestException}
        )
        monkeypatch.setattr(module, "requests", stub)

    return install
