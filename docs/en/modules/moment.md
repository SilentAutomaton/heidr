# moment — question rite

## What it does

Does not read the question at all. Takes the current time and the phase of the
moon.

## Where the data comes from

The system clock and arithmetic. No network and no ephemeris: the phase is
counted from the known new moon of 6 January 2000 in steps of 29.530588853 days,
the mean synodic month.

That count drifts by about an hour per decade, which is more than good enough
for naming a phase.

## How it is processed

The moon's age becomes one of eight names, from new moon to waning crescent. The
name and the timestamp are hashed into the key's number, and the name itself is
the anchor.

## How this rite differs

Like [blind](blind.md) it ignores the words of the question. But where `blind`
discards content for the sake of a double blind, `moment` replaces it with
something else: not what was asked, but when.

Because of the timestamp, the same question asked two minutes apart goes
somewhere else. That still does not allow a second draw — the ledger will not
accept the same question twice.

## Dependencies

None.

## Sources

Nothing borrowed.
