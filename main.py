"""Forwarder so `uv run main.py` works. Real entry point: `uv run rulesync`."""

from rulesync.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
