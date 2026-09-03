# tarot — reading

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/tarot.md)

## What it does

Draws a spread from a seventy-eight card deck and prints each card in a plain
frame with one line of meaning.

## Where the data comes from

The material, and a local file: `heidr/data/tarot.txt`, one line per card.

## How it is processed

1. The material seeds the shuffle, so the same finding always deals the same
   cards. As with `iching`, the randomness was spent when the source
   was consulted.
2. Cards are sampled without replacement, so a spread never repeats a card.
3. Each card is drawn upright or reversed, and gets the matching line.

The frame is drawn from box characters rather than borrowed art, so it renders
the same in a bare console as in a modern terminal.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `deck` | the shipped file | Path to another deck, `name\|upright\|reversed` per line |
| `spread` | `three` | `one` or `three` (before, now, after) |
| `reversals` | `true` | Whether cards can come up reversed |

## Dependencies

None. Standard library only.

## Sources

The card names are traditional and belong to nobody.

**No published readings are shipped.** The interpretations people know — Waite,
Pollack, and every deck's little white book — are under copyright. The two lines
per card in `tarot.txt` were written for this project. Point `deck` at a file of
your own for anything else.

No ASCII art was borrowed. Several MIT-licensed decks exist, among them
[lawreka/ascii-tarot](https://github.com/lawreka/ascii-tarot); none of it is in
this repository.
