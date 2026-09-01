import pytest

from heidr import config
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


def test_settings_list_the_options_of_every_module(default_config):
    keys = [key for key, _line in browser.setting_rows(default_config)]

    assert "modules.fm_voice.dwell_s" in keys
    assert "modules.tarot.spread" in keys
    # Switching a module off belongs to the module list, and only there.
    assert not any(key.endswith(".enabled") for key in keys)


def test_a_module_option_shows_its_default_before_it_is_set(default_config):
    rows = dict(browser.setting_rows(default_config))

    assert "15" in rows["modules.fm_voice.dwell_s"]

    default_config.set("modules.fm_voice.dwell_s", 25)

    assert "25" in dict(browser.setting_rows(default_config))["modules.fm_voice.dwell_s"]


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
async def test_enter_on_a_typed_setting_prefills_the_command_line(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await go_to(pilot, "audio.volume")
        await pilot.press("enter")

        line = pilot.app.query_one("#cmdline")
        assert line.buffer.startswith("set audio.volume=")
        assert pilot.app.edit_mode == "COMMAND"


async def go_to(pilot, key):
    """Walk the cursor to one row, the way a reader would."""
    while pilot.app.rows[pilot.app.cursor][0] != key:
        await pilot.press("down")


@pytest.mark.asyncio
async def test_enter_on_a_named_list_takes_the_next_value(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("enter")

        assert default_config.get("ui.theme") == "full"


@pytest.mark.asyncio
async def test_a_named_list_turns_over_at_the_end(default_config):
    default_config.set("ui.theme", "tty")
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("right")

        assert default_config.get("ui.theme") == "auto"


@pytest.mark.asyncio
async def test_the_left_arrow_goes_back_through_the_values(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("left")

        assert default_config.get("ui.theme") == "tty"


@pytest.mark.asyncio
async def test_enter_on_a_switch_turns_it_over(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await go_to(pilot, "ui.splash")
        await pilot.press("enter")

        assert default_config.get("ui.splash") is False


@pytest.mark.asyncio
async def test_a_module_option_can_be_switched_from_the_list(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await go_to(pilot, "modules.tarot.spread")
        await pilot.press("enter")

        # The module's own default is "three", so the next one is "one".
        assert default_config.get("modules.tarot.spread") == "one"


@pytest.mark.asyncio
async def test_a_typed_setting_says_so_when_the_arrows_are_used(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await go_to(pilot, "audio.volume")
        await pilot.press("right")

        assert "typed" in str(pilot.app.query_one("#cmdline").render())
        assert default_config.get("audio.volume") == 0.6


def test_every_named_list_names_a_real_option(default_config):
    """A table that drifts away from the options is worse than no table."""
    keys = [key for key, _line in browser.setting_rows(default_config)]

    assert set(config.CHOICES) <= set(keys)


def test_every_named_list_holds_its_own_default(default_config):
    rows = dict(browser.setting_rows(default_config))
    for key, choices in config.CHOICES.items():
        assert str(rows[key]).split()[-1] in choices


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


def test_a_short_list_is_shown_whole():
    assert browser.window(5, 0, 10) == (0, 5)
    assert browser.window(5, 4, 5) == (0, 5)


def test_a_long_list_follows_the_cursor():
    assert browser.window(30, 0, 10) == (0, 10)
    assert browser.window(30, 15, 10) == (10, 20)
    assert browser.window(30, 29, 10) == (20, 30)


def test_a_windowed_list_says_where_it_is():
    rows = [(str(index), f"row {index}") for index in range(30)]

    shown = browser.render(rows, cursor=0, empty="", height=5)

    assert shown.splitlines()[-1].strip() == "1-5 of 30"
    assert "row 0" in shown and "row 6" not in shown


@pytest.mark.asyncio
async def test_the_module_list_scrolls_to_the_cursor(default_config):
    async with make_app(default_config).run_test(size=(96, 28)) as pilot:
        await pilot.press("colon", *"modules", "enter")
        for _ in range(25):
            await pilot.press("j")

        shown = str(pilot.app.query_one("#body").content)
        assert pilot.app.rows[pilot.app.cursor][1] in shown


# Moving through a list


@pytest.mark.asyncio
async def test_the_arrows_move_the_cursor(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("down", "down")
        assert pilot.app.cursor == 2

        await pilot.press("up")
        assert pilot.app.cursor == 1


@pytest.mark.asyncio
async def test_the_arrows_move_through_the_menu_too(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("down", "down", "enter")

        assert pilot.app.view == "modules"


@pytest.mark.asyncio
async def test_a_page_moves_by_the_height_of_the_panel(default_config):
    async with make_app(default_config).run_test(size=(100, 30)) as pilot:
        await pilot.press("colon", *"settings", "enter")
        await pilot.press("pagedown")

        wanted = min(pilot.app._room(), len(pilot.app.rows) - 1)
        assert pilot.app.cursor == wanted


@pytest.mark.asyncio
async def test_a_page_stops_at_both_ends(default_config):
    async with make_app(default_config).run_test(size=(100, 30)) as pilot:
        await pilot.press("colon", *"settings", "enter")
        for _ in range(20):
            await pilot.press("pagedown")
        assert pilot.app.cursor == len(pilot.app.rows) - 1

        for _ in range(20):
            await pilot.press("pageup")
        assert pilot.app.cursor == 0
