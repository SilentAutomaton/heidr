# gematria — question module

## What it does

Turns the question into a number by adding up the values of its letters, and
keeps its two longest words as anchors.

## Where the data comes from

The question itself. Nothing else is read.

## How it is processed

1. The text is lowercased.
2. Each letter is scored by its position in the Cyrillic or Latin alphabet.
   Anything else, including digits and punctuation, scores nothing.
3. The sum becomes the key's seed.
4. The two longest words become the anchors a world module will look for.

The same question always gives the same key. This is deliberate: the variation
belongs to the world, not to the arithmetic.

## Dependencies

None. Standard library only.

## Sources

The practice of scoring letters as numbers is older than any implementation of
it and belongs to nobody. Nothing was copied.
