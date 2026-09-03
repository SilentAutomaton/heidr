from concurrent.futures import ThreadPoolExecutor, TimeoutError as Expired

import requests

from heidr.contracts import Unavailable

BUDGET = 12.0
TIMEOUT = 5.0


def fetch_json(url: str, budget: float = BUDGET, timeout: float = TIMEOUT, agent: str = ""):
    """Fetch and decode JSON, or give up within the budget.

    A timeout passed to requests bounds one socket operation, not the whole
    exchange: a slow public endpoint can hold a rite for a minute while never
    exceeding it. So the request is run in a thread and abandoned when the
    budget is spent.
    """
    return _bounded(lambda: _get(url, timeout, agent), url, budget)


def _bounded(work, url: str, budget: float):
    pool = ThreadPoolExecutor(max_workers=1)
    running = pool.submit(work)
    try:
        return running.result(timeout=budget)
    except Expired:
        raise Unavailable(
            f"{_host(url)} did not answer within {budget:.0f} seconds. "
            "The source is slow or unreachable. Draw again, or switch the "
            "module off with :modules."
        ) from None
    except requests.RequestException as failure:
        raise Unavailable(
            f"{_host(url)} could not be read: {failure.__class__.__name__}. "
            "Check the network, then draw again."
        ) from None
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def fetch_text(url: str, budget: float = BUDGET, timeout: float = TIMEOUT, agent: str = "") -> str:
    """The same bounded wait, for a source that is not JSON."""
    return _bounded(lambda: _read(url, timeout, agent), url, budget)


def post_json(url: str, payload: dict, budget: float = BUDGET, timeout: float = TIMEOUT):
    """The same bounded wait, for a request that carries something."""
    return _bounded(lambda: _post(url, payload, timeout), url, budget)


def _get(url: str, timeout: float, agent: str = ""):
    # Some public directories ask callers to name themselves rather than arrive
    # as the default library string, and it costs nothing to oblige.
    headers = {"User-Agent": agent} if agent else None
    reply = requests.get(url, timeout=timeout, headers=headers)
    reply.raise_for_status()
    return reply.json()


def _read(url: str, timeout: float, agent: str = "") -> str:
    headers = {"User-Agent": agent} if agent else None
    reply = requests.get(url, timeout=timeout, headers=headers)
    reply.raise_for_status()
    return reply.text


def _post(url: str, payload: dict, timeout: float):
    reply = requests.post(url, json=payload, timeout=timeout)
    reply.raise_for_status()
    return reply.json()


def _host(url: str) -> str:
    return url.split("/")[2] if "//" in url else url
