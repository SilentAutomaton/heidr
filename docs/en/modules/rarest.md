# rarest — question module

## What it does

Finds the least ordinary word in the question and makes it the only anchor.

## Where the data comes from

The question itself.

## How it is processed

There is no frequency dictionary in this project and there will not be. That is
megabytes for one line of logic. Instead a word's rarity is scored from its
letters: each letter has a place in a list ordered from commonest to rarest, and
the word takes the average.

It is crude but it leans the right way. "Jazz" scores above "the"; "щуплый"
above "это". Function words are made of common letters and lose almost every
time, which is exactly what the score is for.

One anchor, not two as in [gematria](gematria.md). The point is that the world
module looks for precisely one word: the one the question was asked about.

## Dependencies

None.

## Sources

Nothing borrowed.
