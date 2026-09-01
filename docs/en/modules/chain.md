# chain — world module

## What it does

Reads the newest Bitcoin block: its Merkle root for numbers, and whatever
messages people paid to write into it for text.

## Where the data comes from

Two blockchain.info endpoints:

```
https://blockchain.info/latestblock
https://blockchain.info/rawblock/{hash}
```

The second reply is large — a full block with every transaction in it — so the
timeout is generous by default.

## How it is processed

1. The latest block hash is fetched, then the block itself.
2. The **Merkle root** is taken, not the block hash. Mining difficulty forces an
   ever longer run of leading zeros into the block hash, which drains its
   entropy year by year; the Merkle root has no such bias.
3. The root is cut into four eight-character pieces and read as hexadecimal.
   Those are the material's numbers.
4. Every transaction output whose script begins with `6a` — the `OP_RETURN`
   opcode — is decoded as UTF-8 and stripped of unprintable characters. What
   survives becomes the material's text.

`OP_RETURN` is where people write things into the chain on purpose: names,
dates, protocol markers, jokes, memorials. Somebody paid a fee for every one of
them, and none of them were addressed to you.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `timeout` | 15 | Seconds to wait, per request |
| `messages` | 5 | How many `OP_RETURN` payloads to keep |

## Dependencies

`requests`. Network access.

## Sources

The Merkle-root-not-block-hash point comes from
[callebtc/randombtc](https://github.com/callebtc/randombtc). No code was copied.
