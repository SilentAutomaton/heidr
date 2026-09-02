# oblique — reading

## What it does

Draws exactly one terse instruction from a deck and says nothing else.

## Where the data comes from

A flat text file, `heidr/data/strategies.txt`, read from disk. The module never
goes to the network for meaning: a website must not be able to stay silent when
you have asked a question.

## How it is processed

Comment lines and blank lines are ignored. The card is chosen by the material —
the sum of its numbers plus the length of its text, modulo the size of the deck
— so the answer still depends on what was found in the world, not on a fresh
coin toss.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `deck` | the shipped file | Path to another deck, one instruction per line |

## Dependencies

None. Standard library only.

## Sources

The form is the Oblique Strategies of Brian Eno and Peter Schmidt, 1975. **Their
deck is under copyright and is not shipped here.** The cards in
`strategies.txt` were written for this project. Point `deck` at your own file to
use another.

The convention of a flat offline corpus with comment lines comes from
[fortune-mod](https://github.com/shlomif/fortune-mod), ISC.
