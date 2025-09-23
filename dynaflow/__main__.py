"""Entry point for ``python -m dynaflow``."""

from __future__ import annotations

from dynaflow.cli import cli


def main() -> None:
    cli()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()

