"""Allow executing `python -m pixelai` directly from the terminal."""

from pixelai.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
