# mojibake — source

## What it does

Reads random bytes from the kernel and looks at them through the wrong
character encoding, keeping whatever accidentally spells out as letters.

## Where the data comes from

`os.urandom`, which reads the kernel entropy pool. It needs no network, no
hardware and no files, which is what keeps the program working with the dongle
unplugged and the network down.

## How it is processed

1. The key picks one encoding out of `cp1251`, `koi8-r`, `cp1252`, `shift_jis`
   and `cp866`, so the same bytes would read differently on a different draw.
2. Four kilobytes of random bytes are decoded through it, with undecodable
   sequences replaced rather than dropped.
3. Runs of three or more letters are kept and everything else is discarded.
4. The runs become the material's text, their lengths become its numbers.

Nothing here pretends the runs are words. They are the shapes that survive being
read wrongly, which is what the module is for.

## Settings

| Key | Default | Meaning |
|---|---|---|
| `encodings` | five legacy code pages | The pool the key chooses from |
| `bytes` | 4096 | How much randomness to look at |

## Dependencies

None. Standard library only.

## Sources

The idea of reading noise through the wrong code page is folklore among anyone
who has opened a binary file in a text editor. Nothing was copied.
