# blind — question module

## What it does

Throws the question away and keeps only its length.

## Where the data comes from

The number of characters you typed. The words themselves are never used.

## How it is processed

The length is multiplied by a large odd constant so that neighbouring lengths do
not land next to each other, and the result becomes the key's seed. No anchors
are produced, so the world module has nothing to search for and must return
whatever it finds.

This is the double blind case. When it is drawn, nothing you wrote can steer
where the answer comes from, which is the strongest form of the guarantee the
whole program is built on.

## Dependencies

None. Standard library only.

## Sources

Nothing was copied. The idea is the standard double blind arrangement, applied
to divination rather than to a trial.
