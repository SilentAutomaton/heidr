import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# One plain text file per draw, in the manner of dreamdir by Soren Bjornstad
# (MIT). https://github.com/sobjornstad/dreamdir
SUFFIX = ".rite"
WIDTH = 5
HEADER = re.compile(r"^([A-Za-z]+):\s+(.*)$")
GENESIS = "0" * 64


@dataclass
class Entry:
    number: int
    path: Path
    headers: dict[str, str] = field(default_factory=dict)
    body: str = ""

    @property
    def identifier(self) -> str:
        return str(self.number).zfill(WIDTH)

    def get(self, name: str) -> str:
        return self.headers.get(name, "")


def fingerprint(question: str) -> str:
    normalised = " ".join(question.lower().split())
    return hashlib.sha256(normalised.encode()).hexdigest()


class Ledger:
    def __init__(self, directory: Path):
        self.directory = Path(directory).expanduser()
        self.directory.mkdir(parents=True, exist_ok=True)

    def entries(self) -> list[Entry]:
        return [self._read(path) for path in sorted(self.directory.glob(f"*{SUFFIX}"))]

    def last(self) -> Entry | None:
        paths = sorted(self.directory.glob(f"*{SUFFIX}"))
        return self._read(paths[-1]) if paths else None

    def asked_before(self, question: str) -> Entry | None:
        wanted = fingerprint(question)
        for entry in self.entries():
            if entry.get("Question") == wanted:
                return entry
        return None

    def recent_modules(self, rites: int = 3) -> tuple[str, ...]:
        names: list[str] = []
        for entry in self.entries()[-rites:]:
            names.extend(part for part in entry.get("Rite").split("//") if part)
        return tuple(names)

    def commit(self, question: str) -> Entry:
        """Write the promise before the draw, so it cannot be rewritten after."""
        previous = self.last()
        number = previous.number + 1 if previous else 1
        moment = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        question_hash = fingerprint(question)
        entry = Entry(
            number=number,
            path=self.directory / f"{str(number).zfill(WIDTH)}{SUFFIX}",
            headers={
                "Id": str(number).zfill(WIDTH),
                "Date": moment,
                "Status": "open",
                "Rite": "",
                "Question": question_hash,
                "Prev": previous.get("Commit") if previous else GENESIS,
                "Commit": "",
            },
        )
        entry.headers["Commit"] = seal(entry.headers["Prev"], question_hash, moment)
        self._write(entry)
        return entry

    def complete(self, entry: Entry, rite: str, question: str, body: str) -> Entry:
        entry.headers["Status"] = "complete"
        entry.headers["Rite"] = rite
        entry.body = f"{question}\n\n{body}".strip()
        self._write(entry)
        return entry

    def abandon(self, entry: Entry) -> Entry:
        entry.headers["Status"] = "void"
        self._write(entry)
        return entry

    def chain_ok(self) -> bool:
        previous = GENESIS
        for entry in self.entries():
            expected = seal(previous, entry.get("Question"), entry.get("Date"))
            if entry.get("Prev") != previous or entry.get("Commit") != expected:
                return False
            previous = entry.get("Commit")
        return True

    def _write(self, entry: Entry) -> None:
        lines = [f"{name}: {value}" for name, value in entry.headers.items()]
        entry.path.write_text("\n".join(lines) + "\n\n" + entry.body + "\n")

    def _read(self, path: Path) -> Entry:
        headers: dict[str, str] = {}
        lines = path.read_text().splitlines()
        index = 0
        for index, line in enumerate(lines):
            match = HEADER.match(line)
            if not match:
                break
            headers[match.group(1)] = match.group(2)
        return Entry(
            number=int(path.stem),
            path=path,
            headers=headers,
            body="\n".join(lines[index:]).strip(),
        )


def seal(previous: str, question_hash: str, moment: str) -> str:
    # Each entry commits to the one before it, the way a drand round commits to
    # the previous signature. https://github.com/drand/drand
    return hashlib.sha256(f"{previous}{question_hash}{moment}".encode()).hexdigest()
