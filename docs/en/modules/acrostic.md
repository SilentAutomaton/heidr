# acrostic — question rite

## What it does

Collects the first letter of every word into one new word.

## Where the data comes from

The question itself.

## How it is processed

Words are taken without punctuation or digits, the first letter of each is kept,
and the result is joined. That string is hashed into the key's number and is
also the only anchor.

"Should the antenna go" gives `stag`. That is what an acrostic is: meaning the
author did not put there, which is nonetheless objectively present in the text.

The anchor is short and strange, and finding it in the air or on a page is
unlikely. That is fine: a world module that finds no anchor returns what it did
find.

## Dependencies

None.

## Sources

Nothing borrowed. The acrostic is older than all of us.
