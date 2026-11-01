# solar — source

[HEID//R](../../../README.md) · [Documentation](../README.md) · [Modules](../README.md#modules) · [Русский](../../ru/modules/solar.md)

## What it does

Reads the space weather forecast that people at NOAA wrote today, and hands one
paragraph of it to the run, with the last measure of how disturbed the Earth's
magnetic field is. The question gets an answer about a star.

## Where the data comes from

Two public files of the NOAA Space Weather Prediction Center. They need no key
and no account:

```
https://services.swpc.noaa.gov/text/discussion.txt
https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json
```

The first is the forecast discussion, written twice a day. The second is the
planetary K index, measured every three hours.

## How it is processed

1. Header lines, section titles and labels such as `.Forecast...` are removed from
   the discussion. What remains is split into paragraphs.
2. The key's seed selects one paragraph, modulo how many there are. One forecast
   stands for hours, so this is what lets two questions get different text.
3. The paragraph becomes the material's text. The last Kp times one hundred and the
   running A index become its numbers.

A discussion with no paragraphs gives empty material. A file that has changed its
format raises an error. In both cases another source takes the slot.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `discussion` | the first URL | Where to read the forecast |
| `index` | the second URL | Where to read the K index |
| `timeout` | 10 | Seconds to wait |

## Dependencies

`requests`. Network access.

## Sources

Nothing was copied. The text and the data are the work of a United States
government agency, and are in the public domain.
