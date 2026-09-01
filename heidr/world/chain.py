import binascii

import requests

from heidr.contracts import Key, Material
from heidr.registry import world

LATEST = "https://blockchain.info/latestblock"
RAW = "https://blockchain.info/rawblock/{hash}"
OP_RETURN = "6a"


def available(ctx) -> bool:
    return ctx.has("net")


def messages(block: dict, limit: int) -> list[str]:
    """Pull whatever people wrote into OP_RETURN outputs of this block."""
    found: list[str] = []
    for transaction in block.get("tx", []):
        for output in transaction.get("out", []):
            script = output.get("script", "")
            if not script.startswith(OP_RETURN):
                continue
            text = _readable(script[4:])
            if text:
                found.append(text)
            if len(found) >= limit:
                return found
    return found


def _readable(payload: str) -> str:
    try:
        raw = binascii.unhexlify(payload)
    except (binascii.Error, ValueError):
        return ""
    decoded = raw.decode("utf-8", errors="ignore")
    return "".join(character for character in decoded if character.isprintable()).strip()


@world("chain", needs=("net",), defaults={"timeout": 15, "messages": 5})
def run(ctx, key: Key) -> Material:
    timeout = ctx.settings["timeout"]
    latest = requests.get(LATEST, timeout=timeout).json()["hash"]
    block = requests.get(RAW.format(hash=latest), timeout=timeout).json()

    # The block hash loses entropy as mining difficulty pushes leading zeros
    # into it; the Merkle root does not. Pointed out by callebtc/randombtc.
    root = block["mrkl_root"]
    written = messages(block, int(ctx.settings["messages"]))

    ctx.emit("stage", f"chain {block['height']}")
    return Material(
        text=" ".join(written),
        numbers=tuple(int(root[start : start + 8], 16) for start in range(0, 32, 8)),
        source=f"bitcoin/{block['height']}",
        extra={"merkle_root": root, "height": block["height"], "messages": len(written)},
    )
