# skeleton — question rite

## What it does

Drops every vowel from the question and keeps the consonant skeleton.

## Where the data comes from

The question itself.

## How it is processed

The text is split into words, vowels from both alphabets are removed from each,
and anything that comes out empty is discarded. The skeletons are joined, that
string is hashed into the key's number, and the first two become anchors.

The trick is not invented: Semitic writing managed without vowels for a thousand
years and lost nothing that mattered. Vowels carry grammar; consonants carry the
root.

A pleasant side effect follows. The anchor `krsh` matches every inflection of a
word at once. A rite that looks for an exact word trips over grammar; this one
does not.

## Dependencies

None.

## Sources

Nothing borrowed.
