"""HTTP server responsible for exposing the interactive UI."""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from dynaflow.ui.catalogs import CatalogManager
from dynaflow.utils.validator import validate_flow

LOGGER = logging.getLogger(__name__)


class DynaflowUIServer:
    """Expose a lightweight HTTP server that powers the UI."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        *,
        open_browser: bool = False,
        catalog_manager: CatalogManager | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.open_browser = open_browser
        self.catalog_manager = catalog_manager or CatalogManager()
        self.static_dir = Path(__file__).resolve().parent / "static"
        self._httpd: ThreadingHTTPServer | None = None
        self._validate_static_directory()

    def _validate_static_directory(self) -> None:
        """Validate that the static directory exists and contains required files.

        Raises:
            RuntimeError: If static directory or critical files are missing.
        """
        if not self.static_dir.exists():
            raise RuntimeError(f"Static directory not found: {self.static_dir}")

        required_files = ["index.html", "app.js", "styles.css"]
        missing_files = [
            f for f in required_files if not (self.static_dir / f).exists()
        ]

        if missing_files:
            raise RuntimeError(f"Missing static files: {missing_files}")

        LOGGER.info("Static directory validated: %s", self.static_dir)

    # ------------------------------------------------------------------
    def run(self) -> None:
        """Start the server and block the current thread."""

        handler = self._build_handler()
        server = ThreadingHTTPServer((self.host, self.port), handler)
        server.daemon_threads = True
        self._httpd = server

        url = f"http://{self.host}:{self.port}/"
        LOGGER.info("Starting DynaFlow UI at %s", url)
        LOGGER.info("Serving static files from: %s", self.static_dir)
        print(f"DynaFlow UI available at {url}")
        print(f"Static files directory: {self.static_dir}")

        if self.open_browser:
            threading.Thread(
                target=self._open_browser, args=(url,), daemon=True
            ).start()

        try:
            server.serve_forever()
        except KeyboardInterrupt:  # pragma: no cover - manual interruption
            print("\nShutting down DynaFlow UI...")
        finally:
            server.server_close()

    # ------------------------------------------------------------------
    def _open_browser(self, url: str) -> None:
        # Give the server a moment to start
        time.sleep(0.8)
        try:  # pragma: no cover - depends on environment
            webbrowser.open(url, new=2)
        except Exception as exc:
            LOGGER.warning("Unable to open browser: %s", exc)

    def _build_handler(self):
        context = self
        catalog_manager = self.catalog_manager
        static_dir = self.static_dir

        class RequestHandler(SimpleHTTPRequestHandler):
            server_version = "DynaflowUI/1.0"

            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(static_dir), **kwargs)
                LOGGER.debug(
                    "RequestHandler initialized with static_dir: %s", static_dir
                )

            # --------------------------------------------------
            # Routing helpers
            # --------------------------------------------------
            def do_OPTIONS(self):  # noqa: N802 (HTTP verb naming)
                self.send_response(HTTPStatus.NO_CONTENT)
                self._send_cors_headers()
                self.end_headers()

            def do_GET(self):  # noqa: N802 (HTTP verb naming)
                parsed = urllib.parse.urlparse(self.path)
                LOGGER.debug("GET request for path: %s", self.path)

                if parsed.path.startswith("/api/"):
                    self._handle_api_get(parsed)
                    return

                # Handle root path
                if parsed.path in {"/", ""}:
                    LOGGER.debug("Root path requested, redirecting to index.html")
                    self.path = "/index.html"

                # Log the final path and static directory
                LOGGER.debug(
                    "Serving static file: %s from directory: %s", self.path, static_dir
                )

                # Ensure static files are served with proper error handling
                try:
                    super().do_GET()
                except Exception as exc:
                    LOGGER.error("Error serving static file %s: %s", self.path, exc)
                    self.send_error(
                        HTTPStatus.NOT_FOUND, f"File not found: {self.path}"
                    )

            def do_POST(self):  # noqa: N802 (HTTP verb naming)
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path.startswith("/api/"):
                    self._handle_api_post(parsed)
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Unsupported endpoint")

            def do_DELETE(self):  # noqa: N802 (HTTP verb naming)
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path.startswith("/api/catalogs/"):
                    self._handle_api_delete(parsed)
                    return
                self.send_error(HTTPStatus.NOT_FOUND, "Unsupported endpoint")

            # --------------------------------------------------
            # API handlers
            # --------------------------------------------------
            def _handle_api_get(self, parsed: urllib.parse.ParseResult) -> None:
                path = parsed.path
                if path == "/api/health":
                    self._send_json(HTTPStatus.OK, {"status": "ok"})
                    return
                if path == "/api/catalogs":
                    payload = catalog_manager.to_payload()
                    self._send_json(HTTPStatus.OK, payload)
                    return
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "Unknown endpoint", "path": path},
                )

            def _handle_api_post(self, parsed: urllib.parse.ParseResult) -> None:
                path = parsed.path
                if path == "/api/catalogs/install":
                    self._install_catalog()
                    return
                if path.endswith("/refresh") and path.startswith("/api/catalogs/"):
                    alias = self._extract_alias(path, suffix="/refresh")
                    if not alias:
                        self._send_json(
                            HTTPStatus.BAD_REQUEST,
                            {"error": "Invalid catalog alias"},
                        )
                        return
                    try:
                        record = catalog_manager.refresh(alias)
                    except KeyError as exc:
                        self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                        return
                    self._send_json(
                        HTTPStatus.OK,
                        {
                            "catalog": record.to_response(),
                            "functions": catalog_manager.aggregated_functions(),
                        },
                    )
                    return
                if path == "/api/flow/validate":
                    self._validate_flow()
                    return
                self._send_json(
                    HTTPStatus.NOT_FOUND,
                    {"error": "Unknown endpoint", "path": path},
                )

            def _handle_api_delete(self, parsed: urllib.parse.ParseResult) -> None:
                alias = self._extract_alias(parsed.path)
                if not alias:
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "Invalid catalog alias"},
                    )
                    return
                try:
                    catalog_manager.remove(alias)
                except KeyError as exc:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": str(exc)})
                    return
                self.send_response(HTTPStatus.NO_CONTENT)
                self._send_cors_headers()
                self.end_headers()

            # --------------------------------------------------
            # Concrete operations
            # --------------------------------------------------
            def _install_catalog(self) -> None:
                payload = self._read_json_body()
                if payload is None:
                    return

                try:
                    record = catalog_manager.install_catalog(
                        payload.get("pip_url"),
                        alias=payload.get("alias"),
                        module=payload.get("module"),
                        attribute=payload.get("attribute", "function_catalog"),
                        auth=payload.get("auth"),
                    )
                except (ValueError, ImportError) as exc:
                    self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
                    return
                except RuntimeError as exc:
                    self._send_json(
                        HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)}
                    )
                    return

                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "catalog": record.to_response(),
                        "functions": catalog_manager.aggregated_functions(),
                    },
                )

            def _validate_flow(self) -> None:
                payload = self._read_json_body()
                if payload is None:
                    return

                flow = payload.get("flow") or payload
                valid, errors = validate_flow(flow, return_errors=True)
                response = {
                    "valid": bool(valid),
                    "errors": [
                        self._format_validation_error(error) for error in errors
                    ],
                }
                status = HTTPStatus.OK if valid else HTTPStatus.UNPROCESSABLE_ENTITY
                self._send_json(status, response)

            # --------------------------------------------------
            # Helpers
            # --------------------------------------------------
            def _read_json_body(self) -> dict[str, Any] | None:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    self._send_json(
                        HTTPStatus.BAD_REQUEST,
                        {"error": "Invalid JSON payload"},
                    )
                    return None
                return body if isinstance(body, dict) else {"flow": body}

            def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_cors_headers(self) -> None:
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header(
                    "Access-Control-Allow-Headers",
                    "Content-Type, Authorization, X-Requested-With",
                )
                self.send_header(
                    "Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS"
                )

            def _extract_alias(self, path: str, suffix: str = "") -> str | None:
                trimmed = path[len("/api/catalogs/") :]
                if suffix and trimmed.endswith(suffix):
                    trimmed = trimmed[: -len(suffix)]
                trimmed = trimmed.strip("/")
                if not trimmed:
                    return None
                return urllib.parse.unquote(trimmed)

            def _format_validation_error(self, error: Any) -> dict[str, Any]:
                message = getattr(error, "message", str(error))
                path = list(getattr(error, "absolute_path", []))
                validator = getattr(error, "validator", None)
                return {
                    "message": message,
                    "path": path,
                    "validator": validator,
                }

            def log_message(
                self, format: str, *args: Any
            ) -> None:  # noqa: A003 - part of stdlib API
                LOGGER.debug("%s - %s", self.address_string(), format % args)

        return RequestHandler


__all__ = ["DynaflowUIServer"]
