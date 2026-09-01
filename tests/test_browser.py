import pytest

from heidr.ui import browser

from tests.test_app import make_app


def find(rows, key):
    return next(line for row_key, line in rows if row_key == key)


def test_every_module_appears_with_its_slot(stub_context):
    rows = browser.module_rows(stub_context)
    keys = [key for key, _line in rows]

    assert "modules.gematria.enabled" in keys
    assert "modules.babel.enabled" in keys
    assert find(rows, "modules.gematria.enabled").startswith("question ")


def test_a_module_that_cannot_run_says_what_it_needs(stub_context):
    assert "needs sdr" in find(browser.module_rows(stub_context), "modules.rtl_peak.enabled")


def test_a_module_that_can_run_says_so(stub_context):
    assert "ready" in find(browser.module_rows(stub_context), "modules.mojibake.enabled")


def test_switching_a_module_off_shows_and_takes_effect(stub_context):
    stub_context.config.set("modules.mojibake.enabled", False)

    assert "off" in find(browser.module_rows(stub_context), "modules.mojibake.enabled")
    assert browser.enabled(stub_context.config, "mojibake") is False


def test_settings_list_the_configurable_options(default_config):
    rows = browser.setting_rows(default_config)
    keys = [key for key, _line in rows]

    assert "audio.volume" in keys
    assert "llm.provider" in keys
    assert not any(key.startswith("modules.") for key in keys)


def test_the_cursor_marks_one_line():
    rows = [("a", "first"), ("b", "second")]
    shown = browser.render(rows, cursor=1, empty="nothing")

    assert shown.splitlines()[0].startswith("  ")
    assert shown.splitlines()[1].startswith("> ")


def test_an_empty_list_says_so():
    assert browser.render([], 0, "nothing here") == "nothing here"


@pytest.mark.asyncio
async def test_the_module_browser_opens_and_moves(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        assert pilot.app.view == "modules"

        await pilot.press("j", "j")
        assert pilot.app.cursor == 2

        await pilot.press("k")
        assert pilot.app.cursor == 1


@pytest.mark.asyncio
async def test_the_cursor_stops_at_the_ends(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        await pilot.press("k", "k")

        assert pilot.app.cursor == 0


@pytest.mark.asyncio
async def test_enter_switches_a_module_off_and_on(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"modules", "enter")
        key = pilot.app.rows[0][0]

        await pilot.press("enter")
        assert default_config.get(key) is False

        await pilot.press("enter")
        assert default_config.get(key) is True


@pytest.mark.asyncio
async def test_enter_in_settings_prefills_the_command_line(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("enter")

        line = pilot.app.query_one("#cmdline")
        assert line.buffer.startswith("set ui.theme=")
        assert pilot.app.edit_mode == "COMMAND"


@pytest.mark.asyncio
async def test_setting_a_number_stores_a_number(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"set rite.recent_penalty=8", "enter")

        assert default_config.get("rite.recent_penalty") == 8


@pytest.mark.asyncio
async def test_setting_a_flag_stores_a_boolean(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"set ui.splash=false", "enter")

        assert default_config.get("ui.splash") is False


@pytest.mark.asyncio
async def test_write_saves_the_configuration(default_config, tmp_path):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"set ui.theme=tty", "enter")
        await pilot.press("colon", *"w", "enter")

        assert default_config.path.is_file()
        assert "tty" in default_config.path.read_text()
