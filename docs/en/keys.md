# Keys

The program is modal in the manner of neovim, and the keys are the ones a vim
user's hands already know. What follows is the whole map, what it was borrowed
from, and the five places where the two cannot agree.

## Modes

| Mode | What it is | Leaving it |
|---|---|---|
| `NORMAL` | Moving, choosing, running commands | — |
| `INSERT` | Typing the question | `Esc` |
| `COMMAND` | Typing a command after `:` or a search after `/` | `Esc` |

## Asking

| Key | In vim | Here |
|---|---|---|
| `i` `a` `A` `I` `o` `O` | insert at six different places in the line | all open the question field |
| `<space>a` | — | the same, from the menu |
| `:ask`, `:draw` | — | the same |
| `:draw question//world//reading` | — | name the chain instead of leaving it to chance |
| `Ctrl-V` while typing | — | dictate instead of typing |

There is one field and one place in it, so all six do the same thing. That is
not carelessness: the point is that the hand cannot miss.

## Moving

| Key | Here |
|---|---|
| `j` `k`, `Down` `Up` | one line |
| `gg` `G` | the first and the last line |
| `Ctrl-D` `Ctrl-U` | half a screen |
| `Ctrl-F` `Ctrl-B`, `PageDown` `PageUp` | a whole screen |
| `{` `}` | the previous and the next group of settings |
| `Enter` | choose the line under the cursor |
| `Esc`, `Ctrl-O` | back one level; during a run, `Esc` stops it |

## Changing a value

| Key | Here |
|---|---|
| `Enter` | turn a switch over, or take the next of a named set |
| `h` `l`, `Left` `Right` | the previous and the next value |
| `u` `Ctrl-R` | take a setting back, and put it again |
| `:set key=value` | set anything, including what has no named set |
| `:w`, `ZZ` | save the settings; `ZZ` then leaves |

## Searching

| Key | Here |
|---|---|
| `/` | search the lines on screen, case ignored |
| `n` `N` | the next and the previous match, wrapping round |

## The rest

| Key | Here |
|---|---|
| `y` | copy: the answer, an entry, a setting key, whichever is on the panel |
| `-` `+`, `m` | quieter, louder, muted |
| `?`, `:help` | this list |
| `:q`, `ZQ`, `<space>q` | leave |

## Where this and vim cannot agree

Five places, and each is a deliberate choice rather than an oversight.

**`?` is help, and in vim it searches backwards.** Help wins: `?` for help is
close to universal in terminal programs, and `:help` is here as well. Searching
backwards is `N` after a `/`, which is enough for a list.

**`h` and `l` change a value; in vim they move left and right.** There is no
horizontal movement in a list to be had, and a value really is walked left and
right, as `alsamixer` and the setup screen of `htop` also do. The arrow keys
do it too, so the hand finds it blind.

**`Ctrl-U` means two things.** Half a screen up in normal mode, delete the line
while typing. That is exactly what vim does, and the mode is what tells them
apart.

**`m` is mute; in vim it sets a mark.** There are no marks here and there will
be none.

**`q` does nothing.** In vim it records a macro, in `less` it quits, in a vim
help window it closes the window. Any choice would surprise somebody, and
leaving is already `:q`, `ZZ` and `<space>q`.

`d`, `c`, `v`, `p`, `r` and `x` are left unbound on purpose. In vim they are
operators, and there is nothing here for them to operate on; giving them
something unrelated would break the expectation more surely than leaving them
empty.

## Changing them

Everything above is a default. `~/.config/heidr/keymap.toml` overrides any of
it, one section per mode, plus `g` and `Z` for the keys that wait for a second
one. See `keymap.example.toml`.
