# test_path_utils.py
import pytest
import os
import tempfile
from pathlib import Path
from sqlite_rx.utils.path_utils import resolve_database_path

def test_resolve_database_path_memory():
    # Test with :memory: database
    result = resolve_database_path(":memory:", "/data/dir")
    assert result == ":memory:"

def test_resolve_database_path_absolute():
    # Test with absolute path
    path = os.path.abspath("/tmp/test.db")
    result = resolve_database_path(path, "/data/dir")
    assert result == path

def test_resolve_database_path_relative():
    # Test with relative path
    with tempfile.TemporaryDirectory() as temp_dir:
        result = resolve_database_path("test.db", temp_dir)
        expected = os.path.join(temp_dir, "test.db")
        assert str(result) == expected

def test_resolve_database_path_bytes():
    # Test with bytes path
    with tempfile.TemporaryDirectory() as temp_dir:
        path = b"test.db"
        result = resolve_database_path(path, temp_dir)
        expected = os.path.join(temp_dir, "test.db").encode()
        assert result == expected

def test_resolve_database_path_pathlib():
    # Test with Path object
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path("test.db")
        result = resolve_database_path(path, temp_dir)
        expected = Path(temp_dir) / "test.db"
        assert result == expected

def test_resolve_database_path_no_data_dir():
    # Test with no data directory
    path = "test.db"
    result = resolve_database_path(path, None)
    assert result == path