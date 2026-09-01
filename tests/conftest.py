import copy

import pytest

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
    return config.Config(config.merge(config.DEFAULTS, {}), tmp_path / "config.toml")


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
