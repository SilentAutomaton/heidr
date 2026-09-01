from typing import Iterator

import requests

from heidr.llm.base import Message, sse_payloads


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
