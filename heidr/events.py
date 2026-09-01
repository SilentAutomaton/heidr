import threading
from collections import defaultdict
from typing import Any, Callable

Handler = Callable[[Any], None]


class Bus:
    """Modules publish, visualisations subscribe. Neither knows the other."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._lock = threading.Lock()

    def subscribe(self, event: str, handler: Handler) -> Callable[[], None]:
        with self._lock:
            self._handlers[event].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers[event]:
                    self._handlers[event].remove(handler)

        return unsubscribe

    def emit(self, event: str, payload: Any = None) -> None:
        # Capture runs in a worker thread, so the handler list is copied before
        # it is walked and a slow handler cannot block the producer's lock.
        with self._lock:
            handlers = list(self._handlers.get(event, ()))
        for handler in handlers:
            handler(payload)

    def subscribers(self, event: str) -> int:
        with self._lock:
            return len(self._handlers.get(event, ()))
