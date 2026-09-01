import tomllib

from heidr import config


def test_layers_override_in_order(config_dirs, write_config):
    system, user = config_dirs
    write_config(system, '[ui]\ntheme = "full"\nlanguage = "ru"\n')
    write_config(user, '[ui]\ntheme = "tty"\n')

    settings = config.load(user_dir=user, system_dir=system)

    assert settings.get("ui.theme") == "tty"
    assert settings.get("ui.language") == "ru"
    assert settings.get("audio.volume") == config.DEFAULTS["audio"]["volume"]


def test_missing_files_leave_defaults(config_dirs):
    system, user = config_dirs
    settings = config.load(user_dir=user, system_dir=system)
    assert settings.get("llm.provider") == "ollama"
    assert settings.get("nothing.here", "fallback") == "fallback"


def test_module_settings_merge_over_declared_defaults(config_dirs, write_config):
    system, user = config_dirs
    write_config(user, "[modules.fm_voice]\ndwell_s = 9\n")

    settings = config.load(user_dir=user, system_dir=system)
    merged = settings.module("fm_voice", {"dwell_s": 4, "sweep": "random"})

    assert merged == {"dwell_s": 9, "sweep": "random"}


def test_saving_keeps_only_differences(tmp_path):
    pristine = config.Config(config.merge(config.DEFAULTS, {}), tmp_path / "config.toml")
    pristine.set("ui.theme", "tty")
    pristine.set("modules.quake.limit", 3)

    path = config.save(pristine)
    with path.open("rb") as handle:
        written = tomllib.load(handle)

    assert written == {"ui": {"theme": "tty"}, "modules": {"quake": {"limit": 3}}}


def test_secrets_come_from_the_environment(default_config, monkeypatch):
    monkeypatch.setenv("HEIDR_LLM_KEY", "from-env")
    assert default_config.secret("llm.api_key_env") == "from-env"


def test_example_is_copied_once(tmp_path):
    user = tmp_path / "heidr"
    assert config.install_example(user) is not None
    assert config.install_example(user) is None
