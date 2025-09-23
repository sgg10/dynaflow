"""Utilities to manage external function catalogs for the web UI."""

from __future__ import annotations

import importlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
from urllib.parse import quote, urlsplit, urlunsplit

LOGGER = logging.getLogger(__name__)

_DEFAULT_STORAGE = "catalogs.json"


@dataclass
class CatalogRecord:
    """Metadata persisted for an installed catalog."""

    alias: str
    module: str
    pip_url: str | None = None
    attribute: str = "function_catalog"
    metadata: dict[str, Any] = field(default_factory=dict)
    functions: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def dump_config(self) -> dict[str, Any]:
        """Return a serializable representation for persistence."""

        return {
            "alias": self.alias,
            "module": self.module,
            "pip_url": self.pip_url,
            "attribute": self.attribute,
            "metadata": self.metadata,
        }

    def to_response(self) -> dict[str, Any]:
        """Representation exposed through the HTTP API."""

        payload = asdict(self)
        # ``functions`` may include callable references, so make them safe for JSON
        payload["functions"] = [
            {
                **entry,
                "versions": [
                    {**version, "metadata": _make_json_safe(version.get("metadata"))}
                    for version in entry.get("versions", [])
                ],
            }
            for entry in self.functions
        ]
        payload["metadata"] = _make_json_safe(payload.get("metadata"))
        return payload


def _make_json_safe(value: Any) -> Any:
    """Attempt to convert objects into a JSON-friendly representation."""

    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {key: _make_json_safe(item) for key, item in value.items()}
    if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
        return [_make_json_safe(item) for item in value]
    return repr(value)


class CatalogManager:
    """Manage local and remote function catalogs used by the UI."""

    _EGG_REGEX = re.compile(r"#egg=([^&#]+)")

    def __init__(
        self,
        storage_path: str | Path | None = None,
        *,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._records: dict[str, CatalogRecord] = {}
        self._env = env or os.environ
        self._storage_path = Path(storage_path or self._default_storage_path())
        self._function_registry_cls = self._resolve_function_registry()
        self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    @property
    def storage_path(self) -> Path:
        return self._storage_path

    @property
    def supports_function_registry(self) -> bool:
        return self._function_registry_cls is not None

    def list_catalogs(self) -> list[CatalogRecord]:
        with self._lock:
            return [record for record in self._records.values()]

    def aggregated_functions(self) -> list[dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        with self._lock:
            for record in self._records.values():
                for entry in record.functions:
                    name = entry.get("name")
                    if not name:
                        continue
                    group = summary.setdefault(name, {"name": name, "versions": []})
                    for version in entry.get("versions", []):
                        enriched = dict(version)
                        enriched.setdefault("catalog", record.alias)
                        group["versions"].append(enriched)
        return sorted(summary.values(), key=lambda item: item["name"].lower())

    def to_payload(self) -> dict[str, Any]:
        catalogs = [record.to_response() for record in self.list_catalogs()]
        return {
            "catalogs": catalogs,
            "functions": self.aggregated_functions(),
            "supports_registry": self.supports_function_registry,
        }

    def install_catalog(
        self,
        pip_url: str | None,
        *,
        alias: str | None = None,
        module: str | None = None,
        attribute: str = "function_catalog",
        auth: Mapping[str, str] | None = None,
    ) -> CatalogRecord:
        """Install a catalog and persist its configuration."""

        parsed = self._parse_spec(pip_url) if pip_url else {}
        module_name = module or parsed.get("module")
        if not module_name:
            raise ValueError(
                "Module name must be provided either explicitly or within the repository URL."
            )

        alias_name = alias or parsed.get("alias") or module_name

        with self._lock:
            if alias_name in self._records:
                raise ValueError(f"Catalog with alias '{alias_name}' is already registered")

            module_loaded = self._safe_import(module_name)
            if not module_loaded and pip_url:
                self._pip_install(self._build_install_spec(pip_url, auth))
                module_loaded = self._safe_import(module_name)
            if not module_loaded:
                raise ImportError(f"Module '{module_name}' could not be imported")

            record = CatalogRecord(
                alias=alias_name,
                module=module_name,
                pip_url=pip_url,
                attribute=attribute,
                metadata={
                    "source": pip_url,
                    "installed_at": self._current_timestamp(),
                },
            )
            self._refresh_record(record)
            self._records[alias_name] = record
            self._save()
            return record

    def refresh(self, alias: str) -> CatalogRecord:
        with self._lock:
            record = self._records.get(alias)
            if not record:
                raise KeyError(f"Catalog '{alias}' is not registered")
            self._refresh_record(record)
            self._save()
            return record

    def remove(self, alias: str) -> None:
        with self._lock:
            if alias not in self._records:
                raise KeyError(f"Catalog '{alias}' is not registered")
            del self._records[alias]
            self._save()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _default_storage_path(self) -> Path:
        base = self._env.get("DYNAFLOW_UI_HOME")
        if base:
            base_path = Path(base)
        else:
            base_path = Path.home() / ".dynaflow"
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path / _DEFAULT_STORAGE

    def _resolve_function_registry(self):
        try:
            from function_registry import FunctionRegistry  # type: ignore

            return FunctionRegistry
        except Exception:  # pragma: no cover - optional dependency
            return None

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            with self._storage_path.open("r", encoding="utf-8") as stream:
                payload = json.load(stream)
        except json.JSONDecodeError as exc:  # pragma: no cover - extremely rare
            LOGGER.warning("Invalid catalogs cache found at %s: %s", self._storage_path, exc)
            return

        entries = payload.get("catalogs", [])
        if not isinstance(entries, list):
            return

        for raw in entries:
            if not isinstance(raw, Mapping):
                continue
            alias = raw.get("alias")
            module = raw.get("module")
            if not alias or not module:
                continue
            record = CatalogRecord(
                alias=alias,
                module=module,
                pip_url=raw.get("pip_url"),
                attribute=raw.get("attribute", "function_catalog"),
                metadata=dict(raw.get("metadata", {})),
            )
            self._refresh_record(record)
            self._records[alias] = record

    def _save(self) -> None:
        payload = {"catalogs": [record.dump_config() for record in self._records.values()]}
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._storage_path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
        tmp_path.replace(self._storage_path)

    def _refresh_record(self, record: CatalogRecord) -> None:
        try:
            catalog_obj = self._load_catalog_object(record.module, record.attribute)
        except Exception as exc:  # pragma: no cover - best effort
            record.functions = []
            record.error = str(exc)
            LOGGER.warning("Unable to load catalog '%s': %s", record.alias, exc)
            return

        functions, error = self._extract_functions(catalog_obj)
        record.functions = functions
        record.error = error

    def _load_catalog_object(self, module_name: str, attribute: str):
        module = importlib.import_module(module_name)
        try:
            return getattr(module, attribute)
        except AttributeError as exc:  # pragma: no cover - validated at runtime
            raise AttributeError(
                f"Attribute '{attribute}' not found in module '{module_name}'"
            ) from exc

    def _safe_import(self, module_name: str) -> bool:
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    def _pip_install(self, spec: str) -> None:
        LOGGER.info("Installing catalog dependency: %s", spec)
        cmd = [sys.executable, "-m", "pip", "install", spec]
        process = subprocess.run(
            cmd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if process.returncode != 0:
            message = process.stderr.strip() or process.stdout.strip() or "unknown"
            raise RuntimeError(f"Failed to install catalog dependency: {message}")

    def _build_install_spec(
        self, pip_url: str, auth: Mapping[str, str] | None
    ) -> str:
        if not auth:
            return pip_url

        prefix = ""
        url = pip_url
        if pip_url.startswith("git+"):
            prefix = "git+"
            url = pip_url[len("git+") :]

        parts = urlsplit(url)
        if not parts.scheme or not parts.netloc:
            return pip_url

        credential = self._build_credentials(auth)
        if not credential:
            return pip_url

        base_netloc = parts.netloc.split("@", 1)[-1]
        new_netloc = f"{credential}@{base_netloc}"
        rebuilt = urlunsplit(
            (parts.scheme, new_netloc, parts.path, parts.query, parts.fragment)
        )
        return f"{prefix}{rebuilt}"

    def _build_credentials(self, auth: Mapping[str, str]) -> str:
        auth_type = (auth.get("type") or "").lower()
        if auth_type == "basic":
            username = quote(auth.get("username", ""))
            password = quote(auth.get("password", ""))
            if username or password:
                return f"{username}:{password}"
            return ""
        if auth_type == "token":
            token = quote(auth.get("token", ""))
            if not token:
                return ""
            username = auth.get("username")
            if username:
                return f"{quote(username)}:{token}"
            return token

        username = auth.get("username")
        password = auth.get("password")
        token = auth.get("token")
        if username is not None and password is not None:
            return f"{quote(username)}:{quote(password)}"
        if token is not None:
            return quote(token)
        return ""

    def _parse_spec(self, spec: str | None) -> dict[str, str]:
        if not spec:
            return {}

        info: dict[str, str] = {}
        egg_match = self._EGG_REGEX.search(spec)
        if egg_match:
            info["module"] = egg_match.group(1)

        cleaned = spec
        if spec.startswith("git+"):
            cleaned = spec[len("git+") :]

        parts = urlsplit(cleaned)
        path = parts.path or cleaned
        if not info.get("module") and "#egg=" in spec:
            fragment = spec.split("#egg=", 1)[1]
            info["module"] = fragment.split("#", 1)[0]

        if path:
            segment = path.rstrip("/").split("/")[-1]
            segment = segment.split("@", 1)[0]
            if segment.endswith(".git"):
                segment = segment[:-4]
            if segment:
                info.setdefault("alias", segment)
                if "module" not in info:
                    info["module"] = segment.replace("-", "_")

        return info

    def _extract_functions(self, catalog_obj: Any) -> tuple[list[dict[str, Any]], str | None]:
        try:
            raw = self._extract_raw_catalog(catalog_obj)
            functions = self._normalize_functions(raw)
            error = None
        except Exception as exc:  # pragma: no cover - best effort
            functions = []
            error = str(exc)
        return functions, error

    def _extract_raw_catalog(self, catalog_obj: Any) -> Any:
        for attr in ("describe", "export", "to_dict", "summary", "as_dict"):
            candidate = getattr(catalog_obj, attr, None)
            if callable(candidate):
                result = candidate()
                if result:
                    return result

        for attr in ("registry", "_registry", "functions", "_functions"):
            candidate = getattr(catalog_obj, attr, None)
            if candidate:
                return candidate

        if hasattr(catalog_obj, "items"):
            try:
                return dict(catalog_obj.items())
            except Exception:  # pragma: no cover - fall back below
                pass

        if isinstance(catalog_obj, Mapping):
            return dict(catalog_obj)

        if hasattr(catalog_obj, "__iter__"):
            return list(catalog_obj)

        return catalog_obj

    def _normalize_functions(self, raw: Any) -> list[dict[str, Any]]:
        if raw is None:
            return []
        if isinstance(raw, list):
            return [self._normalize_entry(entry) for entry in raw if entry]
        if isinstance(raw, Mapping):
            result = []
            for name, value in raw.items():
                entry = self._normalize_value(name, value)
                if entry:
                    result.append(entry)
            return result
        return []

    def _normalize_entry(self, entry: Any) -> dict[str, Any]:
        if isinstance(entry, Mapping) and "name" in entry:
            name = str(entry["name"])
            versions = entry.get("versions") or []
            normalized_versions = [
                self._build_version(version.get("version"), version)
                for version in versions
                if isinstance(version, Mapping)
            ]
            if not normalized_versions and "function" in entry:
                normalized_versions = [self._build_version(None, entry)]
            return {"name": name, "versions": normalized_versions}
        if isinstance(entry, Mapping):
            return self._normalize_value(entry.get("name", ""), entry)
        if isinstance(entry, str):
            return {"name": entry, "versions": [self._build_version(None, {})]}
        return {"name": repr(entry), "versions": [self._build_version(None, entry)]}

    def _normalize_value(self, name: Any, value: Any) -> dict[str, Any] | None:
        if not name:
            return None
        name_str = str(name)
        if isinstance(value, Mapping):
            versions = []
            if all(isinstance(key, (str, int, float)) for key in value.keys()):
                for version, meta in value.items():
                    versions.append(self._build_version(version, meta))
            else:
                versions.append(self._build_version(None, value))
            return {"name": name_str, "versions": versions or [self._build_version(None, value)]}
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            versions = [self._build_version(None, item) for item in value]
            return {"name": name_str, "versions": versions}
        return {"name": name_str, "versions": [self._build_version(None, value)]}

    def _build_version(self, version: Any, meta: Any) -> dict[str, Any]:
        info: dict[str, Any] = {
            "version": None if version is None else str(version),
            "metadata": {},
        }

        if isinstance(meta, Mapping):
            description = (
                meta.get("description")
                or meta.get("doc")
                or meta.get("summary")
                or meta.get("comment")
            )
            if description:
                info["description"] = str(description)
            if "version" in meta and info["version"] is None:
                info["version"] = str(meta["version"])
            function_obj = meta.get("function")
            if callable(function_obj):
                info["callable_name"] = getattr(function_obj, "__name__", repr(function_obj))
                info["callable_module"] = getattr(function_obj, "__module__", "")
            metadata = {
                key: value
                for key, value in meta.items()
                if key
                not in {
                    "function",
                    "description",
                    "doc",
                    "summary",
                    "comment",
                    "version",
                }
            }
            if metadata:
                info["metadata"] = _make_json_safe(metadata)
        else:
            info["description"] = repr(meta)
            info["metadata"] = _make_json_safe(meta)

        return info

    def _current_timestamp(self) -> str:
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

