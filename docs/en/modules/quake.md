# quake — world module

## What it does

Takes the last hour of earthquakes and hands one of them to the run.

## Where the data comes from

The United States Geological Survey public feed of every earthquake recorded in
the past hour:

```
https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson
```

The feed needs no key and no account, and asks only for ordinary courtesy. The feed usually holds
somewhere between ten and a hundred events.

## How it is processed

1. The feed is fetched and its list of events read.
2. The key's seed selects one of them, modulo however many there are — so the
   choice depends on the question module rather than on a fresh coin toss.
3. The place name becomes the material's text; the magnitude in tenths and the
   depth in kilometres become its numbers; coordinates go into the extras.

A quiet hour is not an error. If the feed is empty, empty material comes back
and the reading works with nothing, which is itself an answer.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `feed` | the URL above | Point at a different feed, for instance the daily one |
| `timeout` | 10 | Seconds to wait |

## Dependencies

`requests`. Network access.

## Sources

Nothing was copied. The idea of using a live public feed of real world events as
material is the same one behind `chain` and `sky`.
