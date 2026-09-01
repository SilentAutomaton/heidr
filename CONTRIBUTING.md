# Contributing

Thanks for looking. The project is small and wants to stay readable.

1. Read [AGENTS.md](AGENTS.md). It applies to people too.
2. Adding a module is the easy path in: see
   [docs/en/module-guide.md](docs/en/module-guide.md). A module is one file, one
   decorator, one function, plus its documentation and one test.
3. Changing the core is the hard path in: read
   [docs/en/architecture.md](docs/en/architecture.md) first and say what you are
   trying to make possible.

Documentation is bilingual. `docs/en/` and `docs/ru/` mirror each other file for
file, and both change in the same commit.

Run `pytest` before you push. Tests that need real hardware or a real network
are marked `live` and are skipped by default.

The project is GPL-3.0-or-later. By contributing you agree your code ships under
that licence.
