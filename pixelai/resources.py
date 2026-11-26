"""Resolve built-in resources in checkouts and installed distributions."""

from pathlib import Path


def library_root():
    package = Path(__file__).resolve().parent
    installed = package / "library"
    return installed if installed.is_dir() else package.parent / "library"
