"""Source-mode entrypoint for `python -m cli`.

Prefer the installed `harness` script after installing the package.
"""
import sys

from interfaces.cli import main


if __name__ == "__main__":
    sys.exit(main())
