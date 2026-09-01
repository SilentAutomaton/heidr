import json
from dataclasses import dataclass
from typing import Iterator, Protocol

from heidr.contracts import Unavailable


@dataclass(frozen=True)
class Message:
    role: str
    content: str

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


class Provider(Protocol):
    name: str

    def stream(self, messages: list[Message]) -> Iterator[str]: ...


def build(config) -> Provider:
    from heidr.llm import anthropic, ollama, openai_compat

    makers = {
        "ollama": ollama.Ollama,
        "openai_compat": openai_compat.OpenAICompatible,
        "anthropic": anthropic.Anthropic,
    }
    chosen = config.get("llm.provider", "")
    if chosen not in makers:
        raise Unavailable(
            f"No language model provider named {chosen!r}. "
            f"Set llm.provider to one of: {', '.join(sorted(makers))}."
        )
    return makers[chosen](config)


def sse_payloads(lines: Iterator[bytes]) -> Iterator[dict]:
    """Read a server sent event stream and yield the JSON of each data line."""
    for line in lines:
        if not line:
            continue
        text = line.decode("utf-8", errors="ignore").strip()
        if not text.startswith("data:"):
            continue
        body = text[5:].strip()
        if body == "[DONE]":
            return
        try:
            yield json.loads(body)
        except json.JSONDecodeError:
            continue


def json_lines(lines: Iterator[bytes]) -> Iterator[dict]:
    """Read newline delimited JSON, the way ollama streams."""
    for line in lines:
        if not line:
            continue
        try:
            yield json.loads(line.decode("utf-8", errors="ignore"))
        except json.JSONDecodeError:
            continue
