import argparse
import random
import sys

import tomli_w

from heidr import __version__, config
from heidr.strings import BANNER_BLOCK, BANNER_PLAIN, NAME, SLOGANS, text


def splash(block_glyphs: bool = True) -> str:
    banner = BANNER_BLOCK if block_glyphs else BANNER_PLAIN
    return f"{banner}\n\n{random.choice(SLOGANS)}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="heidr", description=f"{NAME} terminal oracle")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--splash", action="store_true", help="print the wordmark and exit")
    parser.add_argument("--print-config", action="store_true", help="print the merged configuration")
    args = parser.parse_args(argv)

    if args.splash:
        print(splash())
        return 0

    copied = config.install_example()
    if copied:
        print(text("config.copied", path=copied))

    settings = config.load()

    if args.print_config:
        print(tomli_w.dumps(settings.data).rstrip())
        return 0

    from heidr.app import HeidrApp

    HeidrApp(settings=settings).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
