import pytest

from heidr.app import HeidrApp
from heidr.capabilities import Terminal
from heidr.ui.commandline import CommandLine
from heidr.ui.statusline import StatusLine

FULL = Terminal(colours=16777216, glyphs="braille", graphics="none")
CONSOLE = Terminal(colours=16, glyphs="blocks", graphics="none")


def make_app(default_config, terminal=FULL, user_dir=None):
    return HeidrApp(settings=default_config, user_dir=user_dir, terminal=terminal)


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
