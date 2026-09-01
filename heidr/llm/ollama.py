import socket
from typing import Iterator
from urllib.parse import urlparse

import requests

from heidr.llm.base import Message, Sampling, json_lines


class Ollama:
    name = "ollama"

    def __init__(self, config):
        self.base_url = config.get("llm.base_url", "http://localhost:11434").rstrip("/")
        self.model = config.get("llm.model", "")
        self.timeout = config.get("llm.timeout", 120)
        # A reasoning model given a wall of noise thinks until it runs out of
        # room and answers with nothing at all, so thinking is off by default.
        self.think = bool(config.get("llm.think", False))
        self.sampling = Sampling.from_config(config)
        # A nine billion parameter model takes six seconds to load. Without
        # this the server drops it between rites and every draw pays again.
        self.keep_alive = config.get("llm.keep_alive", "10m")

    def available(self) -> bool:
        # Building the object proves nothing; the daemon has to answer.
        parsed = urlparse(self.base_url)
        try:
            socket.create_connection((parsed.hostname, parsed.port or 11434), timeout=0.4).close()
            return True
        except OSError:
            return False

    def stream(self, messages: list[Message]) -> Iterator[str]:
        reply = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [message.as_dict() for message in messages],
                "stream": True,
                "think": self.think,
                "keep_alive": self.keep_alive,
                "options": {
                    "temperature": self.sampling.temperature,
                    "top_p": self.sampling.top_p,
                    "repeat_penalty": self.sampling.repeat_penalty,
                    "num_ctx": self.sampling.context_tokens,
                    "num_predict": self.sampling.max_tokens,
                },
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
