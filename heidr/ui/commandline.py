from textual.reactive import reactive
from textual.widgets import Static


class CommandLine(Static):
    """The bottom line: a typed command, a typed question, or a message."""

    prefix = reactive("")
    buffer = reactive("")
    message = reactive("")

    def render(self) -> str:
        if self.prefix:
            return f"{self.prefix}{self.buffer}"
        return self.message

    def open(self, prefix: str) -> None:
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

    def say(self, message: str) -> None:
        self.message = message
