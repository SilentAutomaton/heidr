from dataclasses import dataclass, field, replace
from typing import Any, Callable

from heidr.config import Config

CAPABILITIES = ("net", "sdr", "stt", "llm", "audio")


@dataclass(frozen=True)
class Key:
    seed: int
    anchors: tuple[str, ...] = ()


@dataclass(frozen=True)
class Material:
    text: str
    numbers: tuple[int, ...] = ()
    source: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


def _ignore(event: str, payload: Any) -> None:
    pass


@dataclass
class Context:
    config: Config
    capabilities: frozenset[str] = frozenset()
    settings: dict[str, Any] = field(default_factory=dict)
    emit: Callable[[str, Any], None] = _ignore
    llm: Any = None
    stt: Any = None

    def has(self, capability: str) -> bool:
        return capability in self.capabilities

    def with_capabilities(self, *names: str) -> "Context":
        return replace(self, capabilities=self.capabilities | frozenset(names))

    def for_module(self, name: str, defaults: dict[str, Any]) -> "Context":
        return Context(
            config=self.config,
            capabilities=self.capabilities,
            settings=self.config.module(name, defaults),
            emit=self.emit,
            llm=self.llm,
            stt=self.stt,
        )


class Unavailable(Exception):
    pass
