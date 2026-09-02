"""Every user visible string lives here, so a translation is one more table."""

NAME = "HEID//R"
PACKAGE = "heidr"

# The first entry is the primary slogan: it is used wherever only one fits.
# The others are drawn at random on the splash screen.
SLOGANS = (
    "For the Rationally Desperate.",
    "Let Entropy Answer.",
    "Ask the Noise.",
    "Found, Not Written.",
    "One Draw. No Retries.",
    "The World Answers, Not the Model.",
    "The Answer Was Already There.",
    "Listen to What Was Already Said.",
    "Nothing Here Is Generated.",
    "Meaning Is Not Included.",
    "Tune In. Ask Once.",
    "Coincidence, on Demand.",
)

TAGLINE = f"{NAME} — {SLOGANS[0]}"

# Block wordmark for terminals with block glyphs. Each row is split where the
# slashes begin and end, because the slashes are the one thing on the screen
# that is allowed a colour of its own.
BANNER_ROWS = (
    ("█ █ ███ ███ ██ ", "   █   █ ", "██ "),
    ("█ █ █    █  █ █", "  █   █  ", "█ █"),
    ("███ ██   █  █ █", "  █   █  ", "██ "),
    ("█ █ █    █  █ █", " █   █   ", "█ █"),
    ("█ █ ███ ███ ██ ", " █   █   ", "█ █"),
)
BANNER_BLOCK = "\n".join("".join(row) for row in BANNER_ROWS)

# Plain fallback for the Linux console and anything else without block glyphs.
BANNER_PLAIN = NAME

EN = {
    "mode.normal": "NORMAL",
    "mode.insert": "INSERT",
    "mode.command": "COMMAND",
    "prompt.ask": "Ask a question",
    "prompt.choose": "Which {slot}?",
    "prompt.confirm_draw": "Draw the lot",
    "prompt.cancel": "Cancel",
    "empty.ledger": "No draws yet. Type :ask to put a question.",
    "empty.modules": "No modules registered. Something is wrong with the install.",
    "empty.settings": "No settings to show.",
    "empty.material": "Nothing drawn yet. The rite starts with a question.",
    "error.small_terminal": "Terminal too small. Resize to at least {cols} by {rows}.",
    "error.repeat_question": (
        "This question was drawn in entry {entry}. Ask a different one, or ask "
        "this one again a day after that draw."
    ),
    "error.no_voice": (
        "Voice input needs a speech provider. Run :checkhealth to see what is missing."
    ),
    "error.no_modules": (
        "No modules are available here. Run :checkhealth to see what each one needs."
    ),
    "error.unknown_command": "There is no command {name!r}. Type :help for the list.",
    "error.bad_volume": "Volume is a number from 0 to 100, as in :vol 40.",
    "error.bad_setting": "Setting an option needs a value, as in :set ui.theme=tty.",
    "error.already_drawing": "A draw is already running. Press Esc to stop it.",
    "error.slot_exhausted": (
        "No {slot} module could answer. {reason} The question is free again."
    ),
    "error.draw_failed": (
        "The draw stopped before anything was found. The question is free "
        "again, and :checkhealth says what is working."
    ),
    "note.instead": "{failed} could not answer, and {following} was drawn instead.",
    "hint.typed_setting": "This value is typed. Press Enter to edit it.",
    "hint.ask": "Enter asks.  Up and down bring back past questions.  Ctrl-V dictates.",
    "answer.silence_drawn": (
        "The lot fell on silence. One rite in twenty is drawn silent before "
        "anything is read, and this was one of them. What was found above is "
        "the whole of the answer. The question is spent: silence was the answer."
    ),
    "answer.silence_read": (
        "The rite drew mute, and saying nothing is the whole of what mute does. "
        "What was found stands on its own, without a voice over it. The question "
        "is spent: this was an answer."
    ),
    "answer.unread": (
        "Something was found, and no reading could put words to it. {reason} "
        "Nothing was spent — ask the same question again whenever you like."
    ),
    "answer.nothing": (
        "Nothing was found to read. {reason} Nothing was spent, and :checkhealth "
        "says which sources are working here."
    ),
    "answer.stopped": (
        "Stopped on your word, part way through. Nothing was spent — ask again "
        "when you have the time for it."
    ),
    "answer.repeat": (
        "This question was answered in entry {entry}. Ask a different one, or "
        "ask this one again a day after that draw."
    ),
    "note.silence": "silence",
    "note.unread": "unread",
    "note.nothing": "nothing found",
    "note.stopped": "stopped",
    "note.refused": "refused",
    "status.cancelled": "Stopped. The question is free again.",
    "status.stopping": "Stopping at the next step.",
    "status.no_answer": (
        "The reading returned nothing. Only the raw material remains."
    ),
    "status.silent": "The oracle is silent. Only the raw material remains.",
    "status.listening": "Listening",
    "status.waiting": "Waiting",
    "status.done": "Done",
    "status.saved": "Saved to {path}.",
    "config.copied": "Copied the example configuration to {path}. Edit it and restart.",
}

STRINGS = {"en": EN}


def text(key: str, language: str = "en", **fields: object) -> str:
    table = STRINGS.get(language, EN)
    return table[key].format(**fields)
