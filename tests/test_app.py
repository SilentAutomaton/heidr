from pathlib import Path

import pytest

import heidr.__main__ as main_module
from heidr.app import HeidrApp
from heidr.capabilities import Terminal
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine

FULL = Terminal(colours=16777216, glyphs="braille", graphics="none")
CONSOLE = Terminal(colours=16, glyphs="blocks", graphics="none")


def make_app(default_config, terminal=FULL, user_dir=None):
    return HeidrApp(
        settings=default_config,
        user_dir=user_dir or Path("/nonexistent"),
        terminal=terminal,
        capabilities_found=frozenset(),
    )


@pytest.mark.asyncio
async def test_colon_opens_the_command_line(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon")
        assert pilot.app.edit_mode == "COMMAND"
        assert pilot.app.query_one(CommandLine).prefix == ":"


@pytest.mark.asyncio
async def test_escape_returns_to_normal_mode(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", "escape")
        assert pilot.app.edit_mode == "NORMAL"
        assert pilot.app.query_one(CommandLine).prefix == ""


@pytest.mark.asyncio
async def test_typing_a_command_and_running_it(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", "v", "o", "l", "space", "3", "0", "enter")
        assert pilot.app.query_one(StatusLine).volume == 0.3
        assert default_config.get("audio.volume") == 0.3


@pytest.mark.asyncio
async def test_unknown_command_explains_itself(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", "z", "z", "enter")
        assert "Unknown command" in pilot.app.query_one(CommandLine).message


@pytest.mark.asyncio
async def test_leader_then_key_runs_the_leader_action(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("space", "a")
        assert pilot.app.edit_mode == "INSERT"


@pytest.mark.asyncio
async def test_mute_toggles(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("m")
        assert pilot.app.query_one(StatusLine).muted is True
        await pilot.press("m")
        assert pilot.app.query_one(StatusLine).muted is False


@pytest.mark.asyncio
async def test_tiny_terminal_says_so(default_config):
    async with make_app(default_config).run_test(size=(30, 8)) as pilot:
        rendered = pilot.app.query_one("#body").content
        assert "Terminal too small" in str(rendered)


@pytest.mark.asyncio
async def test_keymap_overrides_are_honoured(default_config, tmp_path):
    (tmp_path / "keymap.toml").write_text('[normal]\n"x" = "command_line"\n')
    async with make_app(default_config, user_dir=tmp_path).run_test() as pilot:
        await pilot.press("x")
        assert pilot.app.edit_mode == "COMMAND"


def test_console_terminal_picks_the_tty_stylesheet(default_config):
    app = make_app(default_config, terminal=CONSOLE)
    assert app.css_path[0].name == "theme_tty.tcss"


def test_status_line_drops_fields_as_it_narrows():
    line = StatusLine()
    line.mode = "NORMAL"
    line.rite = "gematria//fm_voice//iching"
    line.provider = "ollama"
    assert "ollama" in line._fit(80)
    assert "ollama" not in line._fit(40)
    assert line._fit(6) == "NORMAL"


@pytest.mark.asyncio
async def test_asking_a_question_runs_a_draw(default_config, monkeypatch):
    from heidr import entropy

    monkeypatch.setattr(entropy, "collect", lambda ctx, seconds=2.0: [])
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *"rain", "enter")
        await pilot.pause()

        assert "//" in pilot.app.query_one(StatusLine).rite
        assert "00001" in str(pilot.app.query_one("#body").content)


@pytest.mark.asyncio
async def test_the_same_question_twice_is_refused(default_config, monkeypatch):
    from heidr import entropy

    monkeypatch.setattr(entropy, "collect", lambda ctx, seconds=2.0: [])
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", *"rain", "enter")
        await pilot.press("i", *"rain", "enter")
        await pilot.pause()

        assert "was drawn in entry" in pilot.app.query_one(CommandLine).message


@pytest.mark.asyncio
async def test_a_broken_provider_removes_the_llm_capability(default_config):
    default_config.set("llm.provider", "telepathy")
    app = HeidrApp(
        settings=default_config,
        user_dir=Path("/nonexistent"),
        terminal=FULL,
        capabilities_found=frozenset({"llm"}),
    )
    async with app.run_test():
        context = app.probe()
        assert "llm" not in context.capabilities
        assert context.llm is None


@pytest.mark.asyncio
async def test_a_working_provider_reaches_the_context(default_config):
    app = HeidrApp(
        settings=default_config,
        user_dir=Path("/nonexistent"),
        terminal=FULL,
        capabilities_found=frozenset({"llm"}),
    )
    async with app.run_test():
        context = app.probe()
        assert context.llm.name == "ollama"


@pytest.mark.asyncio
async def test_volume_keys_move_the_one_output_level(default_config):
    async with make_app(default_config).run_test() as pilot:
        start = pilot.app.levels.volume
        await pilot.press("minus", "minus")

        assert pilot.app.levels.volume < start
        assert pilot.app.query_one(StatusLine).volume == pilot.app.levels.volume
        assert default_config.get("audio.volume") == pilot.app.levels.volume


@pytest.mark.asyncio
async def test_muting_reaches_the_output_and_not_only_the_status_line(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("m")
        assert pilot.app.levels.muted is True

        await pilot.press("colon", *"mute", "enter")
        assert pilot.app.levels.muted is False


@pytest.mark.asyncio
async def test_a_speech_provider_without_a_model_removes_the_capability(default_config):
    app = HeidrApp(
        settings=default_config,
        user_dir=Path("/nonexistent"),
        terminal=FULL,
        capabilities_found=frozenset({"stt"}),
    )
    async with app.run_test():
        context = app.probe()
        assert "stt" not in context.capabilities
        assert context.stt is None


@pytest.mark.asyncio
async def test_voice_input_says_what_is_missing(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("i", "ctrl+v")
        assert "speech provider" in pilot.app.query_one(CommandLine).message


@pytest.mark.asyncio
async def test_an_explicit_capability_set_keeps_providers_out(default_config):
    """A test must never reach a real daemon, so the override is the whole truth."""
    async with make_app(default_config).run_test() as pilot:
        context = pilot.app.probe()

        assert context.capabilities == frozenset()
        assert context.llm is None and context.stt is None


def test_a_built_binary_does_not_check_the_repository_documents(monkeypatch):
    """There is no repository inside a bundle, so there is nothing to check."""
    from heidr.__main__ import _undocumented

    monkeypatch.setattr("sys.frozen", True, raising=False)

    assert _undocumented() == []


def test_the_self_check_builds_the_providers_before_it_reports(default_config, monkeypatch):
    """Whether a model answers cannot be read out of the configuration."""
    from heidr import capabilities

    class Answering:
        name = "fake"

        def __init__(self, settings):
            pass

        def available(self):
            return True

    monkeypatch.setattr("heidr.llm.build", Answering)
    monkeypatch.setattr("heidr.stt.build", Answering)
    monkeypatch.setattr(capabilities, "detect_capabilities", lambda: frozenset())

    printed = []
    monkeypatch.setattr("builtins.print", lambda *parts: printed.append(" ".join(map(str, parts))))
    main_module.self_check(default_config)

    assert any("language model" in line and "fake" in line for line in printed)
