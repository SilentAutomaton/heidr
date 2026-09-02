# planetary — question module

## What it does

Works out which planet rules the current hour and takes the key from it.

## Where the data comes from

The system clock and the configured position. No network and no ephemeris
files: sunrise and sunset are computed here with the ordinary sunrise equation.

## How it is processed

### Planetary hours

The scheme is medieval and elegantly built. Daylight, from sunrise to sunset, is
divided into twelve hours, and the night from sunset to sunrise into twelve
more. So a daylight hour in June is nearly twice a December one, and that
unevenness is not an error but the point.

The rulers follow the Chaldean order — Saturn, Jupiter, Mars, Sun, Venus,
Mercury, Moon — that is, by decreasing apparent speed across the sky. Each hour
takes the next planet along.

The days of the week fall out of the same arithmetic. A day's ruler is the ruler
of its first hour; step twenty four times around a circle of seven and you land
on the next day's planet. That is how Sunday, Monday, Tuesday become Sun, Moon,
Mars. The week we use is a by-product of this counting.

### The key

The planet's name, the hour number and whether it is day or night are hashed
together with the question. The anchor is the planet's name in lower case.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `latitude` | 0.0 | Your position, required |
| `longitude` | 0.0 | Your position, required |

Without a position the module is left out of the choice: sunrise in the Gulf of
Guinea has nothing to do with your day.

## Inside the polar circle

In summer inside the polar circle the sun does not set, in winter it does not
rise, and the sunrise equation has no solution. The module then uses a nominal
six and eighteen hundred. That is not astronomy but a way of not breaking:
planetary hours are simply undefined during a polar day.

## Dependencies

None. Standard library only.

## Sources

Planetary hours are common property and more than a thousand years old. The idea
of making them a question module, and of counting day and night hours separately,
was seen in [Stellium](https://github.com/katelouie/stellium). No code was
copied.
