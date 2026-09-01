import pytest

from heidr import health
from heidr.capabilities import Terminal
from heidr.ledger import Ledger

from tests.test_app import make_app

FULL = Terminal(colours=16777216, glyphs="braille", graphics="kitty")
CONSOLE = Terminal(colours=16, glyphs="blocks", graphics="none")


def named(checks, name):
    return next(check for check in checks if check.name == name)


def test_a_bare_console_is_a_warning_not_a_failure():
    check = health._terminal(CONSOLE)

    assert check.state == health.WARN
    assert "bare console" in check.detail


def test_a_capable_terminal_passes():
    assert health._terminal(FULL).state == health.OK


def test_a_missing_radio_says_what_to_do(stub_context):
    check = health._radio(stub_context)

    assert check.state == health.WARN
    assert "Plug in the dongle" in check.detail


def test_a_present_radio_passes(stub_context):
    assert health._radio(stub_context.with_capabilities("sdr")).state == health.OK


def test_a_missing_model_explains_the_consequence(stub_context):
    assert "still work" in health._llm(stub_context).detail
    assert "no voice input" in health._speech(stub_context).detail


def test_a_verified_ledger_reports_its_size(tmp_path):
    ledger = Ledger(tmp_path / "ledger")
    entry = ledger.commit("one")
    ledger.complete(entry, "a//b//c", "one", "answer")

    check = health._ledger(ledger)

    assert check.state == health.OK
    assert "1 entries" in check.detail


def test_a_tampered_ledger_is_a_failure(tmp_path):
    ledger = Ledger(tmp_path / "ledger")
    entry = ledger.commit("one")
    ledger.complete(entry, "a//b//c", "one", "answer")
    entry.path.write_text(entry.path.read_text().replace("Question: ", "Question: 00"))

    check = health._ledger(ledger)

    assert check.state == health.FAIL
    assert "edited by hand" in check.detail


def test_every_slot_is_reported(stub_context):
    names = [check.name for check in health._modules(stub_context)]

    assert names == ["slot question", "slot world", "slot reading"]


def test_a_slot_with_nothing_usable_fails(stub_context, temporary_slot):
    checks = health._modules(stub_context)

    assert all(check.state == health.FAIL for check in checks)
    assert "No rite can be drawn" in checks[0].detail


def test_the_report_renders_one_line_per_check(stub_context):
    checks = health.report(stub_context, CONSOLE)
    lines = health.as_text(checks).splitlines()

    assert len(lines) == len(checks)
    assert all(line[0] in "+~-" for line in lines)


@pytest.mark.asyncio
async def test_checkhealth_fills_the_body(default_config):
    async with make_app(default_config).run_test() as pilot:
        await pilot.press("colon", *"checkhealth", "enter")

        shown = str(pilot.app.query_one("#body").content)
        assert "terminal" in shown and "slot world" in shown
