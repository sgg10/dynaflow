from __future__ import annotations

from pathlib import Path

from dynaflow.ui.catalogs import CatalogManager


def create_manager(tmp_path: Path) -> CatalogManager:
    storage = tmp_path / "catalogs.json"
    return CatalogManager(storage_path=storage)


def test_install_and_remove_local_catalog(tmp_path):
    manager = create_manager(tmp_path)

    record = manager.install_catalog(
        pip_url=None,
        alias="demo",
        module="tests.sample_catalog",
        attribute="function_catalog",
    )

    assert record.alias == "demo"
    assert record.functions, "functions should be extracted"
    assert record.error is None

    catalogs = manager.list_catalogs()
    assert len(catalogs) == 1
    assert catalogs[0].alias == "demo"

    aggregated = manager.aggregated_functions()
    assert aggregated
    assert aggregated[0]["name"] == "demo_function"
    versions = {version["version"] for version in aggregated[0]["versions"]}
    assert {"1", "2"} <= versions

    refreshed = manager.refresh("demo")
    assert refreshed.functions

    manager.remove("demo")
    assert not manager.list_catalogs()


def test_parse_git_spec_infers_metadata(tmp_path):
    manager = create_manager(tmp_path)
    spec = "git+https://example.com/team/catalog.git@main#egg=my_catalog"
    parsed = manager._parse_spec(spec)  # noqa: SLF001 - testing helper
    assert parsed["module"] == "my_catalog"
    assert parsed["alias"] == "catalog"


def test_build_install_spec_injects_auth(tmp_path):
    manager = create_manager(tmp_path)
    spec = "git+https://example.com/repo.git"
    result = manager._build_install_spec(  # noqa: SLF001 - testing helper
        spec,
        {"type": "basic", "username": "user", "password": "pass"},
    )
    assert "user:pass" in result
