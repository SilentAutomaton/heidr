from datetime import datetime, timedelta, timezone

from heidr.ledger import GENESIS, Ledger, fingerprint, seal


def test_numbers_are_fixed_width_and_increase(tmp_path):
    ledger = Ledger(tmp_path)
    first = ledger.commit("first question")
    ledger.complete(first, "a//b//c", "first question", "answer")
    second = ledger.commit("second question")

    assert first.identifier == "00001"
    assert second.identifier == "00002"
    assert second.path.name == "00002.rite"


def test_the_commitment_is_written_before_the_answer(tmp_path):
    ledger = Ledger(tmp_path)
    entry = ledger.commit("will it rain")

    written = entry.path.read_text()
    assert fingerprint("will it rain") in written
    assert "Status: open" in written
    assert "will it rain" not in written


def test_the_same_question_in_other_words_is_still_the_same(tmp_path):
    ledger = Ledger(tmp_path)
    entry = ledger.commit("Will   it RAIN")
    ledger.complete(entry, "a//b//c", "Will it rain", "no")

    assert ledger.asked_before("will it rain").identifier == "00001"
    assert ledger.asked_before("will it snow") is None


def test_the_chain_holds_across_entries(tmp_path):
    ledger = Ledger(tmp_path)
    for question in ("one", "two", "three"):
        entry = ledger.commit(question)
        ledger.complete(entry, "a//b//c", question, "answer")

    assert ledger.chain_ok()
    assert ledger.entries()[0].get("Prev") == GENESIS


def test_a_tampered_entry_is_caught(tmp_path):
    ledger = Ledger(tmp_path)
    entry = ledger.commit("one")
    ledger.complete(entry, "a//b//c", "one", "answer")

    text = entry.path.read_text().replace(f"Question: {fingerprint('one')}", "Question: " + "f" * 64)
    entry.path.write_text(text)

    assert not ledger.chain_ok()


def test_a_released_draw_frees_the_question(tmp_path):
    ledger = Ledger(tmp_path)
    ledger.abandon(ledger.commit("interrupted"), released=True)

    assert ledger.asked_before("interrupted") is None
    assert ledger.last().get("Status") == "void"


def test_a_broken_draw_leaves_the_question_free(tmp_path):
    """No answer arrived, so nothing was spent, whatever was found on the way."""
    ledger = Ledger(tmp_path)
    ledger.abandon(ledger.commit("interrupted"), released=False)

    assert ledger.asked_before("interrupted") is None
    assert ledger.last().get("Status") == "broken"


def test_what_gave_way_is_written_down(tmp_path):
    ledger = Ledger(tmp_path)
    entry = ledger.commit("what now")
    ledger.complete(entry, "a//b//c", "what now", "an answer", ("quake", "sky"))

    assert ledger.last().get("Instead") == "quake, sky"
    assert ledger.chain_ok()


def test_recent_modules_come_from_the_last_rites(tmp_path):
    ledger = Ledger(tmp_path)
    for index, rite in enumerate(("a//b//c", "d//e//f", "g//h//i", "j//k//l")):
        entry = ledger.commit(f"question {index}")
        ledger.complete(entry, rite, f"question {index}", "answer")

    assert ledger.recent_modules(3) == ("d", "e", "f", "g", "h", "i", "j", "k", "l")


def test_the_body_survives_a_round_trip(tmp_path):
    ledger = Ledger(tmp_path)
    entry = ledger.commit("what now")
    ledger.complete(entry, "a//b//c", "what now", "line one\nline two")

    stored = Ledger(tmp_path).last()
    assert stored.body == "what now\n\nline one\nline two"


# The hold on a question lasts a day


def dated(ledger, question: str, hours_ago: float):
    """One completed entry, written as though it happened that long ago."""
    entry = ledger.commit(question)
    ledger.complete(entry, "a//b//c", question, "answer")
    moment = (datetime.now(timezone.utc).astimezone() - timedelta(hours=hours_ago)).isoformat(
        timespec="seconds"
    )
    entry.headers["Date"] = moment
    # The seal covers the date, so moving the date means sealing it again;
    # otherwise this helper would only be testing the tamper check.
    entry.headers["Commit"] = seal(entry.get("Prev"), entry.get("Question"), moment)
    ledger._write(entry)
    return entry


def test_a_question_asked_an_hour_ago_is_still_spent(tmp_path):
    ledger = Ledger(tmp_path)
    dated(ledger, "how will today go", 1)

    assert ledger.asked_before("how will today go") is not None


def test_a_question_asked_yesterday_can_be_asked_again(tmp_path):
    ledger = Ledger(tmp_path)
    dated(ledger, "how will today go", 25)

    assert ledger.asked_before("how will today go") is None


def test_the_old_entry_stays_where_it_is(tmp_path):
    ledger = Ledger(tmp_path)
    old = dated(ledger, "how will today go", 25)
    again = ledger.commit("how will today go")
    ledger.complete(again, "a//b//c", "how will today go", "another answer")

    assert len(ledger.entries()) == 2
    assert ledger.entries()[0].get("Date") == old.get("Date")
    assert ledger.chain_ok()


def test_a_damaged_date_keeps_the_question_spent(tmp_path):
    ledger = Ledger(tmp_path)
    entry = dated(ledger, "how will today go", 25)
    entry.headers["Date"] = "not a date at all"
    ledger._write(entry)

    assert ledger.asked_before("how will today go") is not None


def test_without_a_window_a_question_is_spent_for_good(tmp_path):
    ledger = Ledger(tmp_path)
    dated(ledger, "how will today go", 24 * 365)

    assert ledger.asked_before("how will today go", within=None) is not None


def test_a_void_draw_is_free_whatever_the_date(tmp_path):
    ledger = Ledger(tmp_path)
    entry = ledger.commit("how will today go")
    ledger.abandon(entry, released=True)

    assert ledger.asked_before("how will today go", within=None) is None
