from typing import Iterator

import requests

from heidr.llm.base import Message, json_lines


class Ollama:
    name = "ollama"

    def __init__(self, config):
        self.base_url = config.get("llm.base_url", "http://localhost:11434").rstrip("/")
        self.model = config.get("llm.model", "")
        self.timeout = config.get("llm.timeout", 120)

    def stream(self, messages: list[Message]) -> Iterator[str]:
        reply = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [message.as_dict() for message in messages],
                "stream": True,
            },
            timeout=self.timeout,
            stream=True,
        )
        reply.raise_for_status()
        for payload in json_lines(reply.iter_lines()):
            piece = payload.get("message", {}).get("content", "")
            if piece:
                yield piece
            if payload.get("done"):
                return
