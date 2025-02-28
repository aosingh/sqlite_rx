# sqlite_rx/tests/misc/test_health_check.py
import time
import pytest
import os
import signal
import logging
import socket
import platform
import tempfile
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer
from sqlite_rx.multiserver import SQLiteMultiServer

LOG = logging.getLogger(__name__)

def test_server_health_check():
    """Test the health check API for SQLiteServer."""
    # Start a server
    server = SQLiteServer(
        bind_address="tcp://127.0.0.1:15678",
        database=":memory:"
    )
    server.start()
    
    try:
        # Give server time to initialize
        time.sleep(0.5)
        
        # Create a client
        client = SQLiteClient(connect_address="tcp://127.0.0.1:15678")
        
        # Call health check command
        result = client.execute("HEALTH_CHECK")
        
        # Verify result contains expected fields
        assert "status" in result
        assert result["status"] == "healthy"
        assert "uptime" in result
        assert "version" in result
        assert "database_status" in result
        
        # Check if database is responsive
        assert result["database_status"] == "connected"
        assert "memory_database" in result
        assert result["memory_database"] is True
        
        # Make a few queries to test metrics
        client.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        client.execute("INSERT INTO test (value) VALUES (?)", ("test1",))
        client.execute("SELECT * FROM test")
        
        # Wait for the metrics to update
        time.sleep(0.1)
        
        # Call health check again to check metrics
        result = client.execute("HEALTH_CHECK")
        assert "query_count" in result
        assert result["query_count"] >= 3  # At least our 3 queries
        
        # Clean up
        client.cleanup()
    finally:
        # Stop the server
        try:
            os.kill(server.pid, signal.SIGTERM)
            server.join(timeout=2)
        except Exception as e:
            LOG.warning(f"Error terminating server: {e}")

def test_server_health_check_with_file_db():
    """Test the health check API with a file-based database."""
    # Create a temporary file for the database
    with tempfile.NamedTemporaryFile(suffix='.db') as temp_db:
        # Start a server with a file DB
        server = SQLiteServer(
            bind_address="tcp://127.0.0.1:15679",
            database=temp_db.name
        )
        server.start()
        
        try:
            # Give server time to initialize
            time.sleep(0.5)
            
            # Create a client
            client = SQLiteClient(connect_address="tcp://127.0.0.1:15679")
            
            # Call health check command
            result = client.execute("HEALTH_CHECK")
            
            # Verify database info
            assert "memory_database" in result
            assert result["memory_database"] is False
            assert "database_path" in result
            assert temp_db.name in result["database_path"]
            
            # Clean up
            client.cleanup()
        finally:
            # Stop the server
            try:
                os.kill(server.pid, signal.SIGTERM)
                server.join(timeout=2)
            except Exception as e:
                LOG.warning(f"Error terminating server: {e}")

def test_multiserver_health_check():
    """Test the health check API for SQLiteMultiServer."""
    # Skip on non-Unix platforms as multiserver is more complex to clean up
    if platform.system() == "Windows":
        pytest.skip("Skipping on Windows due to process cleanup issues")
    
    # Start a multi-server
    server = SQLiteMultiServer(
        bind_address="tcp://127.0.0.1:15680",
        default_database=":memory:",
        database_map={"test": ":memory:"}
    )
    server.start()
    
    try:
        # Create clients
        default_client = SQLiteClient(connect_address="tcp://127.0.0.1:15680")
        test_client = SQLiteClient(connect_address="tcp://127.0.0.1:15680", database_name="test")
        
        # Wait for server to be ready
        time.sleep(1)
        
        # Call health check on default database
        default_result = default_client.execute("HEALTH_CHECK")
        
        # Basic verification of health check fields
        assert "status" in default_result
        assert default_result["status"] == "healthy"
        assert "server_type" in default_result
        assert default_result["server_type"] == "SQLiteMultiServer"
        assert "processes" in default_result
        
        # Call health check on test database
        test_result = test_client.execute("HEALTH_CHECK")
        
        # Verify results
        assert test_result["status"] == "healthy"
        
        # Check for database-specific information
        assert default_result["database_name"] == ""  # Default database
        assert test_result["database_name"] == "test"
        
        # Check presence of processes info
        assert len(default_result["processes"]) >= 2  # At least default and test
        assert "default" in default_result["processes"]
        assert "test" in default_result["processes"]
        
        # Make some queries and check if metrics update
        default_client.execute("CREATE TABLE test_default (id INTEGER PRIMARY KEY, value TEXT)")
        test_client.execute("CREATE TABLE test_specific (id INTEGER PRIMARY KEY, value TEXT)")
        
        # Give time for metrics to update
        time.sleep(0.1)
        
        # Check health again
        updated_default = default_client.execute("HEALTH_CHECK")
        updated_test = test_client.execute("HEALTH_CHECK")
        
        # Verify query counts increased
        assert updated_default["metrics"]["query_count"] > 0
        assert updated_test["metrics"]["query_count"] > 0
        
        # Clean up
        default_client.cleanup()
        test_client.cleanup()
        
    finally:
        # Stop the server and all database processes
        try:
            os.kill(server.pid, signal.SIGTERM)
            server.join(timeout=2)
        except Exception as e:
            LOG.warning(f"Error terminating server: {e}")
