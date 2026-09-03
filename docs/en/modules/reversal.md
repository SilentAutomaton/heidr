# reversal — question module

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/reversal.md)

## What it does

Asks a language model to rewrite the question as its opposite, and takes the key
from what comes back.

## Where the data comes from

The question and the configured provider. Nothing else is sent.

## How it is processed

The instruction is short: same subject, same length, reversed intent, and the
rewritten question only. "Should the antenna go on the roof" becomes "should the
antenna stay off the roof".

After that it is ordinary: the rewritten question's hash becomes the key's
number and its first two words become anchors.

## Does this break the rule

The project's rule is that the model interprets what was found and never
selects it. Here the model works before anything has been found, which is a
different thing.

It rewrites the question — it changes where the gaze is pointed. What is in that
direction is still the world's business: the key leads to a page, a frequency or
an aircraft overhead, and the model knows nothing about that and never will.

With no provider configured the module is left out of the choice.

## Dependencies

A working [language model](../llm.md) provider.

Capabilities: [`llm`](../llm.md).

## Sources

Nothing borrowed.
