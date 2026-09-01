from concurrent.futures import ThreadPoolExecutor, TimeoutError as Expired

import requests

from heidr.contracts import Unavailable

BUDGET = 12.0
TIMEOUT = 5.0


def fetch_json(url: str, budget: float = BUDGET, timeout: float = TIMEOUT):
    """Fetch and decode JSON, or give up within the budget.

    A timeout passed to requests bounds one socket operation, not the whole
    exchange: a slow public endpoint can hold a rite for a minute while never
    exceeding it. So the request is run in a thread and abandoned when the
    budget is spent.
    """
    pool = ThreadPoolExecutor(max_workers=1)
    running = pool.submit(_get, url, timeout)
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


def _get(url: str, timeout: float):
    reply = requests.get(url, timeout=timeout)
    reply.raise_for_status()
    return reply.json()


def _host(url: str) -> str:
    return url.split("/")[2] if "//" in url else url
