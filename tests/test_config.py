from smm.core.config import (
    normalize_path, resolve_collection_name, add_watch_dir,
    SMM_DIR, DEFAULT_CONFIG,
)


class TestNormalizePath:
    def test_absolute_path(self):
        result = normalize_path("/home/user/docs")
        assert result.endswith("/home/user/docs")

    def test_tilde_expansion(self):
        result = normalize_path("~/docs")
        assert result.startswith("/")
        assert "docs" in result

    def test_relative_path(self):
        result = normalize_path(".")
        assert result.startswith("/")


class TestResolveCollectionName:
    def test_simple_dir(self):
        cfg = {"watch_dirs": []}
        name = resolve_collection_name("/home/user/notes", cfg)
        assert name == "notes"

    def test_no_conflict(self):
        cfg = {"watch_dirs": [{"path": "/a", "collection": "existing"}]}
        name = resolve_collection_name("/home/user/docs", cfg)
        assert name == "docs"

    def test_conflict_resolution(self):
        cfg = {"watch_dirs": [{"path": "/a", "collection": "docs"}]}
        name = resolve_collection_name("/home/user/docs", cfg)
        assert name != "docs"
        assert "docs" in name.lower()


class TestAddWatchDir:
    def test_add_new_dir(self, tmp_path, monkeypatch):
        import tempfile, os
        cfg = {"watch_dirs": []}
        with tempfile.TemporaryDirectory() as td:
            cfg = add_watch_dir(cfg, td, "test_coll")
            assert len(cfg["watch_dirs"]) == 1
            assert cfg["watch_dirs"][0]["collection"] == "test_coll"

    def test_no_duplicate(self, tmp_path):
        import tempfile
        cfg = {"watch_dirs": []}
        with tempfile.TemporaryDirectory() as td:
            cfg = add_watch_dir(cfg, td, "test_coll")
            cfg = add_watch_dir(cfg, td, "test_coll")
            assert len(cfg["watch_dirs"]) == 1
