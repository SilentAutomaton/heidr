"""Every user visible string lives here, so a translation is one more table."""

NAME = "HEID//R"
PACKAGE = "heidr"

# The first entry is the primary slogan: it is used wherever only one fits.
# The others are drawn at random on the splash screen.
SLOGANS = (
    "For the Rationally Desperate.",
    "Let Entropy Answer.",
    "Ask the Noise.",
)

TAGLINE = f"{NAME} — {SLOGANS[0]}"

# Block wordmark for terminals with block glyphs.
BANNER_BLOCK = "\n".join(
    (
        "█ █ ███ ███ ██    █   █ ██ ",
        "█ █ █    █  █ █  █   █  █ █",
        "███ ██   █  █ █  █   █  ██ ",
        "█ █ █    █  █ █ █   █   █ █",
        "█ █ ███ ███ ██  █   █   █ █",
    )
)

# Plain fallback for the Linux console and anything else without block glyphs.
BANNER_PLAIN = NAME

EN = {
    "mode.normal": "NORMAL",
    "mode.insert": "INSERT",
    "mode.command": "COMMAND",
    "prompt.ask": "Ask a question",
    "prompt.confirm_draw": "Draw the lot",
    "prompt.cancel": "Cancel",
    "empty.ledger": "No draws yet. Type :ask to put a question.",
    "empty.material": "Nothing drawn yet. The rite starts with a question.",
    "error.small_terminal": "Terminal too small. Resize to at least {cols} by {rows}.",
    "error.repeat_question": (
        "This question was drawn before, in entry {entry}. Ask a different one."
    ),
    "error.no_voice": (
        "Voice input needs a speech provider. Run :checkhealth to see what is missing."
    ),
    "error.no_modules": (
        "No modules are available here. Run :checkhealth to see what each one needs."
    ),
    "status.silent": "The oracle is silent. Only the raw material remains.",
    "status.listening": "Listening",
    "status.waiting": "Waiting",
    "status.done": "Done",
    "config.copied": "Copied the example configuration to {path}. Edit it and restart.",
}

STRINGS = {"en": EN}


def text(key: str, language: str = "en", **fields: object) -> str:
    table = STRINGS.get(language, EN)
    return table[key].format(**fields)
