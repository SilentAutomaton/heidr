import pytest

from heidr import config


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
