import socket
from typing import Iterator
from urllib.parse import urlparse

import requests

from heidr.llm.base import Message, Sampling, sse_payloads


class OpenAICompatible:
    """One client for every service that speaks /v1/chat/completions.

    That includes the llama.cpp server, OpenAI itself, and the several hosted
    services that copied its shape.
    """

    name = "openai_compat"

    def __init__(self, config):
        self.base_url = config.get("llm.base_url", "http://localhost:8080").rstrip("/")
        self.model = config.get("llm.model", "")
        self.timeout = config.get("llm.timeout", 120)
        self.key = config.secret("llm.api_key_env")
        # Only what this shape understands; the rest is ollama's own.
        self.sampling = Sampling.from_config(config)

    def available(self) -> bool:
        parsed = urlparse(self.base_url)
        if parsed.hostname not in ("localhost", "127.0.0.1"):
            return bool(self.key)
        try:
            socket.create_connection((parsed.hostname, parsed.port or 8080), timeout=0.4).close()
            return True
        except OSError:
            return False

    def headers(self) -> dict[str, str]:
        found = {"content-type": "application/json"}
        if self.key:
            found["authorization"] = f"Bearer {self.key}"
        return found

    def stream(self, messages: list[Message]) -> Iterator[str]:
        reply = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json={
                "model": self.model,
                "messages": [message.as_dict() for message in messages],
                "stream": True,
                "temperature": self.sampling.temperature,
                "top_p": self.sampling.top_p,
                "max_tokens": self.sampling.max_tokens,
            },
            headers=self.headers(),
            timeout=self.timeout,
            stream=True,
        )
        reply.raise_for_status()
        for payload in sse_payloads(reply.iter_lines()):
            for choice in payload.get("choices", []):
                piece = choice.get("delta", {}).get("content") or ""
                if piece:
                    yield piece
