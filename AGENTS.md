# Working on HEID//R

Read this before changing anything. It is short on purpose; the detail lives in
`docs/en/`.

## Read first

| Before you | Read |
|---|---|
| write any code | [docs/en/codestyle.md](docs/en/codestyle.md) |
| add a module | [docs/en/module-guide.md](docs/en/module-guide.md) |
| write a test | [docs/en/testing.md](docs/en/testing.md) |
| change the core | [docs/en/architecture.md](docs/en/architecture.md) |

Every document has a Russian mirror in `docs/ru/` with the same file name. When
you change one, change the other in the same commit.

The two languages are held to different standards. English documents use plain
technical English. Russian documents use proper literary Russian — connected
prose, full sentences, technical terms only where they earn their place. Neither
is a word-for-word rendering of the other. The rules are in
[docs/en/codestyle.md](docs/en/codestyle.md#documentation-language).

## Hard rules

1. **The camera is never used.** Not for entropy, not for anything. The
   microphone is used only to dictate a question, and only when a speech
   provider is configured.
2. **The language model interprets, it never chooses.** The moment a model picks
   the material instead of reading it, the program stops being an oracle.
3. **Nothing personal is committed.** No API keys, no home paths, no ledger
   entries, no downloaded models. The repository ships `*.example` files only.
4. **A module ships with its documentation and its tests in the same commit.**
   `tools/check_docs.py` fails the build otherwise.
5. **Borrowed code keeps its header.** Author, link, original license. If the
   licence does not allow the copy, reimplement and credit the idea instead.

## Commits

One step, one commit. The message is a single line of plain English describing
what the code now does:

```
add network world modules
```

No tool names, no model names, no attribution trailers.

## Before you commit

```
pytest
python -m heidr --self-check
git diff --cached          # look for keys and personal paths
```
