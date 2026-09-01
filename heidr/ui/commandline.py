from rich.text import Text
from textual.reactive import reactive
from textual.widgets import Static

MARKER = "!"
INFO, ERROR = "info", "error"


class CommandLine(Static):
    """The bottom line: a typed command, a typed question, or a message."""

    prefix = reactive("")
    buffer = reactive("")
    message = reactive("")
    level = reactive(INFO)
    accent = reactive("yellow")
    echo = reactive(True)

    def render(self) -> Text:
        if self.prefix and self.echo:
            return Text(f"{self.prefix}{self.buffer}")
        if self.level == ERROR and self.message:
            # Something went wrong, and the one line that says so is at the
            # very bottom of the screen: it gets the accent and a marker, so it
            # is not read as another "setting changed".
            return Text(f"{MARKER}  {self.message}", self.accent)
        return Text(self.message)

    def open(self, prefix: str) -> None:
        self.echo = True
        self.prefix = prefix
        self.buffer = ""
        self.message = ""

    def close(self) -> str:
        typed = self.buffer
        self.prefix = ""
        self.buffer = ""
        return typed

    def type(self, character: str) -> None:
        self.buffer += character

    def backspace(self) -> None:
        self.buffer = self.buffer[:-1]

    def say(self, message: str, level: str = INFO) -> None:
        self.level = level
        self.message = message
