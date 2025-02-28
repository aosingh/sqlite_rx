# sqlite_rx/tests/misc/test_auto_connect.py
import os
import time
import pytest
import tempfile
import signal
import logging
import shutil
from pathlib import Path

from sqlite_rx.client import SQLiteClient
from sqlite_rx.multiserver import SQLiteMultiServer

LOG = logging.getLogger(__name__)

def test_auto_connect_existing_database():
    """Test the auto-connect feature with existing databases."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a database file that already exists
        test_db_path = os.path.join(temp_dir, "existing.db")
        
        # Create an empty database file
        import sqlite3
        conn = sqlite3.connect(test_db_path)
        conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, value TEXT)")
        conn.execute("INSERT INTO test_table (value) VALUES (?)", ("pre-existing data",))
        conn.commit()
        conn.close()
        
        # Start server with auto_connect enabled but auto_create disabled
        server = SQLiteMultiServer(
            bind_address="tcp://127.0.0.1:15800",
            default_database=":memory:",
            data_directory=temp_dir,
            auto_connect=True,
            auto_create=False,
            max_connections=3
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(0.5)
            
            # Connect to the existing database
            client = SQLiteClient(
                connect_address="tcp://127.0.0.1:15800", 
                database_name="existing"
            )
            
            # Verify we can query the pre-existing data
            result = client.execute("SELECT * FROM test_table")
            assert len(result["items"]) == 1
            assert result["items"][0][1] == "pre-existing data"
            
            # Check health info includes this dynamically connected database
            health = client.execute("HEALTH_CHECK")
            assert "dynamic_databases" in health
            assert "existing" in health["dynamic_databases"]
            
            # Clean up
            client.cleanup()
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")

def test_auto_create_database():
    """Test the auto-create feature for non-existent databases."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Start server with both auto_connect and auto_create enabled
        server = SQLiteMultiServer(
            bind_address="tcp://127.0.0.1:15801",
            default_database=":memory:",
            data_directory=temp_dir,
            auto_connect=True,
            auto_create=True,
            max_connections=3
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(0.5)
            
            # Connect to a non-existent database that should be auto-created
            client = SQLiteClient(
                connect_address="tcp://127.0.0.1:15801", 
                database_name="new_database"
            )
            
            # Create a table and insert data
            client.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            client.execute("INSERT INTO test_table (name) VALUES (?)", ("Auto-created data",))
            
            # Verify data was inserted
            result = client.execute("SELECT * FROM test_table")
            assert len(result["items"]) == 1
            assert result["items"][0][1] == "Auto-created data"
            
            # Check that the database file was actually created
            db_path = os.path.join(temp_dir, "new_database.db")
            assert os.path.exists(db_path)
            
            # Clean up
            client.cleanup()
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")

def test_auto_create_disabled():
    """Test that auto-create prevents creation of new databases when disabled."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Start server with auto_connect enabled but auto_create disabled
        server = SQLiteMultiServer(
            bind_address="tcp://127.0.0.1:15802",
            default_database=":memory:",
            data_directory=temp_dir,
            auto_connect=True,
            auto_create=False,
            max_connections=3
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(0.5)
            
            # Connect to a non-existent database
            client = SQLiteClient(
                connect_address="tcp://127.0.0.1:15802", 
                database_name="nonexistent"
            )
            
            # Attempt to create a table - should fail
            result = client.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT)")
            
            # Verify we got an error
            assert result["error"] is not None
            assert "Database 'nonexistent' not found" in result["error"]["message"]
            
            # Check that no database file was created
            db_path = os.path.join(temp_dir, "nonexistent.db")
            assert not os.path.exists(db_path)
            
            # Clean up
            client.cleanup()
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")

def test_connection_limit_and_lru():
    """Test that connection limit works and least recently used connections are evicted."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Start server with a small connection limit
        server = SQLiteMultiServer(
            bind_address="tcp://127.0.0.1:15803",
            default_database=":memory:",
            data_directory=temp_dir,
            auto_connect=True,
            auto_create=True,
            max_connections=2  # Only allow 2 dynamic connections
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(0.5)
            
            # Create three databases (beyond the limit of 2)
            client1 = SQLiteClient(connect_address="tcp://127.0.0.1:15803", database_name="db1")
            client1.execute("CREATE TABLE t1 (id INTEGER PRIMARY KEY)")
            client1.execute("INSERT INTO t1 (id) VALUES (1)")
            
            client2 = SQLiteClient(connect_address="tcp://127.0.0.1:15803", database_name="db2")
            client2.execute("CREATE TABLE t2 (id INTEGER PRIMARY KEY)")
            client2.execute("INSERT INTO t2 (id) VALUES (2)")
            
            # At this point both db1 and db2 should be in the cache
            
            # Create a query to db3, which should evict db1 (the least recently used)
            client3 = SQLiteClient(connect_address="tcp://127.0.0.1:15803", database_name="db3")
            client3.execute("CREATE TABLE t3 (id INTEGER PRIMARY KEY)")
            client3.execute("INSERT INTO t3 (id) VALUES (3)")
            
            # Check health to see which connections are active
            health = client1.execute("HEALTH_CHECK")
            
            # We should see db2 and db3 in the active connections
            assert "dynamic_databases" in health
            active_dbs = [db["database_name"] for db in health["dynamic_databases"].values()]
            assert "db2" in active_dbs
            assert "db3" in active_dbs
            assert "db1" not in active_dbs  # db1 should have been evicted
            
            # Now access db1 again - it should reconnect
            result = client1.execute("SELECT * FROM t1")
            assert len(result["items"]) == 1
            
            # This should now have evicted db2
            health = client1.execute("HEALTH_CHECK")
            active_dbs = [db["database_name"] for db in health["dynamic_databases"].values()]
            assert "db1" in active_dbs
            assert "db3" in active_dbs
            assert "db2" not in active_dbs  # db2 should now be evicted
            
            # Clean up
            client1.cleanup()
            client2.cleanup()
            client3.cleanup()
            
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")
