from pathlib import Path

LIMIT = 200


class History:
    """What was typed before, kept the way a shell keeps it.

    The line being written is not lost while the past is looked through: it is
    held aside and comes back at the bottom of the list, as in neovim.
    """

    def __init__(self, path: Path, limit: int = LIMIT):
        self.path = Path(path).expanduser()
        self.limit = limit
        self.lines = self._read()
        self.cursor = len(self.lines)
        self.pending = ""

    def _read(self) -> list[str]:
        if not self.path.is_file():
            return []
        kept = [line for line in self.path.read_text(encoding="utf-8").splitlines() if line]
        return kept[-self.limit :]

    def add(self, line: str) -> None:
        line = line.strip()
        # A line repeated straight away is one line, not two.
        if line and (not self.lines or self.lines[-1] != line):
            self.lines.append(line)
            self.lines = self.lines[-self.limit :]
            self._write()
        self.cursor = len(self.lines)
        self.pending = ""

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")

    def back(self, typed: str) -> str:
        if not self.lines:
            return typed
        if self.cursor == len(self.lines):
            self.pending = typed
        self.cursor = max(0, self.cursor - 1)
        return self.lines[self.cursor]

    def forward(self) -> str:
        if self.cursor >= len(self.lines):
            return self.pending
        self.cursor += 1
        if self.cursor == len(self.lines):
            return self.pending
        return self.lines[self.cursor]
