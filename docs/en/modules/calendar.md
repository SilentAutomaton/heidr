# calendar — question module

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/calendar.md)

## What it does

Converts today's date into one of three unfamiliar calendars and takes the key
from the result.

## Where the data comes from

The system clock. Everything else is arithmetic.

## Three reckonings

**Discordian.** Five seasons of seventy three days — Chaos, Discord, Confusion,
Bureaucracy and The Aftermath — counted from 1166 BC. In a leap year St Tib's
Day is inserted between the sixtieth and sixty first days, belonging to no
season. `ddate` lived with this inside `util-linux` for two decades before being
thrown out for frivolity.

**French Republican.** Twelve months of thirty days named after what the fields
were doing, from Vendémiaire to Fructidor, plus five extra days at the year's
end. Counted from 22 September 1792.

There is a subtlety here. The decree set the year to begin on the true autumn
equinox, and following that needs an ephemeris. We use Romme's arithmetic rule —
leap years as in the Gregorian calendar — as does everyone who has implemented
this calendar in software. The divergence from the decree begins in the
twenty second century.

**Maya long count.** Simply the number of days since a fixed morning, written in
baktun, katun, tun, winal and kin. The Goodman-Martinez-Thompson correlation;
easy to check, since 21 December 2012 comes out as exactly 13.0.0.0.0 — the date
there was so much noise about.

## How it is processed

By default the calendar changes daily: the day number modulo three. Nobody
chooses which reckoning a question is dated in, and a question asked tomorrow
lands in a different one.

The calendar's name and the resulting date are hashed with the question. The
anchor is the calendar's name.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `which` | `rotate` | `discordian`, `republican`, `long_count`, or rotate |

## Dependencies

None.

## Sources

The Discordian reckoning comes from [ddate](https://github.com/bo0ts/ddate),
whose author signed himself Druel the Chaotic. Romme's rule and the GMT
correlation are well known formulae. No code was copied from anywhere.
