# embed — question module

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/embed.md)

## What it does

Turns the question into a vector with an embedding model and folds that vector
into the key's number.

## Where the data comes from

The question and a local ollama daemon at `/api/embeddings`. The default model
is `nomic-embed-text`.

The module works with ollama only: ordinary chat providers do not serve
embeddings, and carrying a second client for it would not be worth the weight.
With any other provider the module is left out of the choice.

## How it is processed

A vector is a direction in several hundred dimensions, not a quantity. Adding up
its components means nothing, so the vector is hashed whole.

Only one property is needed: the same question always arrives at the same place,
and near-identical questions do not. A hash gives that. An attempt to "add the
meaning up into a number" would give only the appearance of it.

The anchors remain the question's first two words.

## How it differs from gematria

[gematria](gematria.md) counts letters; `embed` counts meaning, or what a model
takes for meaning. Both are deterministic and both ignore the world. The
difference is that a reworded question gives gematria an entirely different
number, and the embedding a neighbouring vector — but still a different hash.

So there is no promise here that similar questions lead to similar places. There
is only the honest "this question leads where it leads".

## Settings

| Key | Default | Meaning |
|---|---|---|
| `model` | `nomic-embed-text` | Any embedding model ollama knows |
| `timeout` | 20 | Seconds to wait |

## Dependencies

A running ollama with an embedding model pulled.

Capabilities: [`llm`](../llm.md).

## Sources

Nothing borrowed.
