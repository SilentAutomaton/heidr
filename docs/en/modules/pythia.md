# pythia — reading

## What it does

Hands the finding to a language model and streams back what it says, in a voice
that is itself drawn by lot.

## Where the data comes from

The material, the question, and whichever provider `llm.provider` names. Nothing
else is sent — not the ledger, not your other questions, not the machine.

## How it is processed

1. A voice is chosen from six: a pythia, a Roman augur, a Sufi teacher, a Zen
   teacher, a cartographer, an investigator. The material decides which, so the
   same finding always gets the same treatment.
2. The system message tells the model who it is and, more importantly, what it
   may not do: use only what is in the fragment, invent nothing further, do not
   hedge, at most six lines.
3. The material is formatted as a small labelled block — source, numbers, text —
   the way `Kerykeion` prepares astrological data for a model, separately from
   the form a person reads.
4. Tokens are yielded as they arrive.

## The limit

**The model interprets. It does not choose.** It is never asked which page to
open, which frequency to listen to, or which of several findings to prefer. By
the time it is called, the finding is already fixed and already written into the
ledger's commitment. The model reads it and nothing else.

This module is left out of the choice when no provider is configured, so an
program with no model still works: it picks one of the readings that
needs nothing.

## Settings

None of its own. It uses the `[llm]` section. See [llm.md](../llm.md).

## Dependencies

A working language model provider: ollama, an OpenAI-compatible endpoint, or
Anthropic.

## Sources

The idea of formatting found data into a block prepared for a model, kept apart
from the human readable form, comes from
[Kerykeion](https://github.com/g-battaglia/kerykeion). No code was copied.
