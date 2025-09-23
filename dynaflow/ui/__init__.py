"""DynaFlow web UI utilities."""

from __future__ import annotations

from .server import DynaflowUIServer

__all__ = ["DynaflowUIServer", "run_ui"]


def run_ui(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> None:
    """Start the built-in web UI server.

    Args:
        host: Interface where the server will listen for connections.
        port: TCP port used by the HTTP server.
        open_browser: When ``True`` the default browser is opened automatically
            pointing to the generated URL.
    """

    server = DynaflowUIServer(host=host, port=port, open_browser=open_browser)
    server.run()

