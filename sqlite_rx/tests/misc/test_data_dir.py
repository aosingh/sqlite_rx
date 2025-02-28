# sqlite_rx/tests/misc/test_data_directory.py
import os
import time
import pytest
import tempfile
import shutil
import socket
import signal
import logging
from pathlib import Path
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer
from sqlite_rx.multiserver import SQLiteMultiServer

LOG = logging.getLogger(__name__)

def test_server_data_directory():
    """Test SQLiteServer with specified data directory."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = "test_database.db"  # Relative path
        abs_db_path = os.path.join(temp_dir, db_path)
        
        # Start a server with data directory
        server = SQLiteServer(
            bind_address="tcp://127.0.0.1:15690",
            database=db_path,
            data_directory=temp_dir
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(0.5)
            
            # Create a client
            client = SQLiteClient(connect_address="tcp://127.0.0.1:15690")
            
            # Run some queries to create data
            client.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
            client.execute("INSERT INTO test (value) VALUES (?)", ("test data",))
            
            # Verify the database file was created in the specified location
            assert os.path.exists(abs_db_path), f"Database file not found at {abs_db_path}"
            
            # Query data to make sure it's accessible
            result = client.execute("SELECT * FROM test")
            assert len(result["items"]) == 1
            assert result["items"][0][1] == "test data"
            
            # Check health info includes data directory
            health = client.execute("HEALTH_CHECK")
            assert "data_directory" in health
            assert health["data_directory"] == temp_dir
            
            # Clean up
            client.cleanup()
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")

def test_multiserver_data_directory():
    """Test SQLiteMultiServer with specified data directory."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Relative database paths
        default_db = "default.db"
        users_db = "users.db"
        products_db = "products.db"
        
        # Full paths for verification
        default_path = os.path.join(temp_dir, default_db)
        users_path = os.path.join(temp_dir, users_db)
        products_path = os.path.join(temp_dir, products_db)
        
        # Set up database map
        database_map = {
            "users": users_db,
            "products": products_db
        }
        
        # Start a multi-server with data directory
        server = SQLiteMultiServer(
            bind_address="tcp://127.0.0.1:15691",
            default_database=default_db,
            database_map=database_map,
            data_directory=temp_dir
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(1)
            
            # Create clients for each database
            default_client = SQLiteClient(connect_address="tcp://127.0.0.1:15691")
            users_client = SQLiteClient(connect_address="tcp://127.0.0.1:15691", database_name="users")
            products_client = SQLiteClient(connect_address="tcp://127.0.0.1:15691", database_name="products")
            
            # Create tables in each database
            default_client.execute("CREATE TABLE default_table (id INTEGER PRIMARY KEY, name TEXT)")
            users_client.execute("CREATE TABLE users_table (id INTEGER PRIMARY KEY, username TEXT)")
            products_client.execute("CREATE TABLE products_table (id INTEGER PRIMARY KEY, product_name TEXT)")
            
            # Insert data
            default_client.execute("INSERT INTO default_table (name) VALUES (?)", ("Default Data",))
            users_client.execute("INSERT INTO users_table (username) VALUES (?)", ("User1",))
            products_client.execute("INSERT INTO products_table (product_name) VALUES (?)", ("Product1",))
            
            # Verify database files were created in the specified location
            assert os.path.exists(default_path), f"Default database not found at {default_path}"
            assert os.path.exists(users_path), f"Users database not found at {users_path}"
            assert os.path.exists(products_path), f"Products database not found at {products_path}"
            
            # Query data to make sure it's accessible
            default_result = default_client.execute("SELECT * FROM default_table")
            users_result = users_client.execute("SELECT * FROM users_table")
            products_result = products_client.execute("SELECT * FROM products_table")
            
            assert len(default_result["items"]) == 1
            assert len(users_result["items"]) == 1
            assert len(products_result["items"]) == 1
            
            # Check health info includes data directory
            health = default_client.execute("HEALTH_CHECK")
            assert "data_directory" in health
            assert health["data_directory"] == temp_dir
            
            # Clean up clients
            default_client.cleanup()
            users_client.cleanup()
            products_client.cleanup()
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")

def test_absolute_and_relative_paths_mixing():
    """Test mixing absolute and relative paths with data directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create another temp dir for absolute path database
        abs_db_dir = tempfile.mkdtemp()
        try:
            # Relative path
            rel_db = "relative.db"
            rel_db_path = os.path.join(temp_dir, rel_db)
            
            # Absolute path
            abs_db = os.path.join(abs_db_dir, "absolute.db")
            
            # Start a server with data directory
            server = SQLiteMultiServer(
                bind_address="tcp://127.0.0.1:15692",
                default_database=rel_db,  # Relative path
                database_map={
                    "abs": abs_db,  # Absolute path
                },
                data_directory=temp_dir
            )
            server.start()
            
            try:
                # Give server time to initialize
                time.sleep(1)
                
                # Create clients
                rel_client = SQLiteClient(connect_address="tcp://127.0.0.1:15692")
                abs_client = SQLiteClient(connect_address="tcp://127.0.0.1:15692", database_name="abs")
                
                # Create tables and insert data
                rel_client.execute("CREATE TABLE rel_table (id INTEGER PRIMARY KEY, data TEXT)")
                abs_client.execute("CREATE TABLE abs_table (id INTEGER PRIMARY KEY, data TEXT)")
                
                rel_client.execute("INSERT INTO rel_table (data) VALUES (?)", ("Relative DB Data",))
                abs_client.execute("INSERT INTO abs_table (data) VALUES (?)", ("Absolute DB Data",))
                
                # Verify files were created in correct locations
                assert os.path.exists(rel_db_path), f"Relative database not found at {rel_db_path}"
                assert os.path.exists(abs_db), f"Absolute database not found at {abs_db}"
                
                # Query data
                rel_result = rel_client.execute("SELECT * FROM rel_table")
                abs_result = abs_client.execute("SELECT * FROM abs_table")
                
                assert len(rel_result["items"]) == 1
                assert len(abs_result["items"]) == 1
                
                # Clean up
                rel_client.cleanup()
                abs_client.cleanup()
            finally:
                # Stop the server
                try:
                    os.kill(server.pid, signal.SIGTERM)
                    server.join(timeout=2)
                except Exception as e:
                    LOG.warning(f"Error terminating server: {e}")
        finally:
            # Clean up absolute path temp directory
            shutil.rmtree(abs_db_dir, ignore_errors=True)
