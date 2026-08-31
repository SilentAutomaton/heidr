import argparse
import random
import sys

from heidr import __version__
from heidr.strings import BANNER_BLOCK, BANNER_PLAIN, NAME, SLOGANS


def splash(block_glyphs: bool = True) -> str:
    banner = BANNER_BLOCK if block_glyphs else BANNER_PLAIN
    return f"{banner}\n\n{random.choice(SLOGANS)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="heidr", description=f"{NAME} terminal oracle")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--splash", action="store_true", help="print the wordmark and exit")
    args = parser.parse_args(argv)

    if args.splash:
        print(splash())
        return 0

    print(f"{NAME} {__version__}: the interface is not built yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
