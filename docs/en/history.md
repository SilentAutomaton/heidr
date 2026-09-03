# Input history

[HEID//R](../../README.md) · [Documentation](README.md) · [Русский](../ru/history.md)

Two files under `~/.local/share/heidr`: `commands` and `questions`. They are
looked through apart, because a command and a question are not the same kind of
thing and mixing them makes both harder to find.

`Up` and `Down`, or `Ctrl-P` and `Ctrl-N`, walk the list in insert and command
modes. A line repeated straight away is kept once, an empty line is not kept at
all, and only the last two hundred survive.

The line being written is held aside while the past is looked through, and it
comes back at the bottom of the list. That is how neovim behaves, and losing
half a typed question to a stray arrow key would be its own small betrayal.

The location is `history.path` in the configuration.
