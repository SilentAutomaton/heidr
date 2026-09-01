from typing import Iterator

import requests

from heidr.contracts import Unavailable
from heidr.llm.base import Message, Sampling, sse_payloads

VERSION = "2023-06-01"


class Anthropic:
    name = "anthropic"

    def __init__(self, config):
        self.base_url = config.get("llm.base_url", "https://api.anthropic.com").rstrip("/")
        self.model = config.get("llm.model", "")
        self.timeout = config.get("llm.timeout", 120)
        self.sampling = Sampling.from_config(config)
        self.key = config.secret("llm.api_key_env")
        self.key_name = config.get("llm.api_key_env", "")

    def available(self) -> bool:
        return bool(self.key)

    def stream(self, messages: list[Message]) -> Iterator[str]:
        if not self.key:
            raise Unavailable(
                f"No API key for the language model. The {self.key_name} "
                "environment variable is empty. Export it and start again."
            )

        # The system prompt travels in its own field here, not as a message.
        system = " ".join(m.content for m in messages if m.role == "system")
        talk = [m.as_dict() for m in messages if m.role != "system"]

        reply = requests.post(
            f"{self.base_url}/v1/messages",
            json={
                "model": self.model,
                "max_tokens": self.sampling.max_tokens,
                "temperature": self.sampling.temperature,
                "top_p": self.sampling.top_p,
                "system": system,
                "messages": talk,
                "stream": True,
            },
            headers={
                "content-type": "application/json",
                "x-api-key": self.key,
                "anthropic-version": VERSION,
            },
            timeout=self.timeout,
            stream=True,
        )
        reply.raise_for_status()
        for payload in sse_payloads(reply.iter_lines()):
            if payload.get("type") == "content_block_delta":
                piece = payload.get("delta", {}).get("text", "")
                if piece:
                    yield piece
