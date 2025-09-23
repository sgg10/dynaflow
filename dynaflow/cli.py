"""Command line interface for DynaFlow."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from dynaflow.ui import DynaflowUIServer
from dynaflow.ui.catalogs import CatalogManager


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="[%(levelname)s] %(name)s: %(message)s")


@click.group()
@click.option("--verbose", is_flag=True, help="Enable verbose logging output")
def cli(verbose: bool) -> None:
    """Manage DynaFlow utilities from the command line."""

    _configure_logging(verbose)


@cli.command(help="Launch the interactive web UI")
@click.option("--host", default="127.0.0.1", show_default=True, help="Host interface")
@click.option("--port", default=8765, show_default=True, help="Port where the server will listen")
@click.option(
    "--open-browser/--no-open-browser",
    default=False,
    show_default=True,
    help="Open the default browser automatically",
)
@click.option(
    "--home",
    type=click.Path(file_okay=False, dir_okay=True, writable=True, path_type=Path),
    default=None,
    help=(
        "Directory used to persist UI metadata. "
        "Defaults to ~/.dynaflow when not provided."
    ),
)
def ui(host: str, port: int, open_browser: bool, home: Path | None) -> None:
    storage_path = None
    if home is not None:
        home.mkdir(parents=True, exist_ok=True)
        storage_path = home / "catalogs.json"

    manager = CatalogManager(storage_path=storage_path)
    server = DynaflowUIServer(
        host=host,
        port=port,
        open_browser=open_browser,
        catalog_manager=manager,
    )

    try:
        server.run()
    except OSError as exc:  # pragma: no cover - depends on environment
        raise click.ClickException(str(exc)) from exc


__all__ = ["cli"]

