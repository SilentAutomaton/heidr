from textual.reactive import reactive
from textual.widgets import Static

SEPARATOR = "  "


class StatusLine(Static):
    mode = reactive("NORMAL")
    rite = reactive("")
    volume = reactive(0.6)
    muted = reactive(False)
    provider = reactive("")

    def render(self) -> str:
        return self._fit(self.size.width or 80)

    def _fit(self, width: int) -> str:
        # Fields drop from the right as the terminal narrows; the mode is last
        # to go, because without it a modal interface is unreadable.
        fields = [self.mode, self.rite, self._volume_field(), self.provider]
        while fields:
            line = SEPARATOR.join(field for field in fields if field)
            if len(line) <= width:
                return line
            fields.pop()
        return self.mode[:width]

    def _volume_field(self) -> str:
        if self.muted:
            return "muted"
        return f"vol {round(self.volume * 100)}"
