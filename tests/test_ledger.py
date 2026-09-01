from heidr.ledger import GENESIS, Ledger, fingerprint


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


def test_a_broken_draw_still_spends_the_question(tmp_path):
    ledger = Ledger(tmp_path)
    ledger.abandon(ledger.commit("interrupted"), released=False)

    assert ledger.asked_before("interrupted") is not None
    assert ledger.last().get("Status") == "broken"


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
