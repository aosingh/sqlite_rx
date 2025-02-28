
import os
import platform
import signal
import time
import pytest
import sqlite3
import logging.config
import socket
import subprocess

from sqlite_rx import get_default_logger_settings
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger(__file__)

def wait_for_server(host, port, timeout=10):
    """Wait for server to be available on the given port."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host, port))
            s.close()
            return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
        finally:
            try:
                s.close()
            except:
                pass
    return False

def kill_process(pid, timeout=5):
    """Kill a process with a timeout for graceful shutdown."""
    try:
        # Try graceful termination first
        os.kill(pid, signal.SIGTERM)
        
        # Check if process exists with timeout
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Check if process still exists
                os.kill(pid, 0)
                time.sleep(0.1)
            except OSError:
                # Process no longer exists
                return True
        
        # If we get here, process didn't terminate gracefully, force kill
        os.kill(pid, signal.SIGKILL)
        return True
    except Exception as e:
        LOG.error(f"Error killing process {pid}: {e}")
        return False

@pytest.fixture(scope="module")
def plain_client():
    auth_config = {
        sqlite3.SQLITE_OK: {
            sqlite3.SQLITE_DROP_TABLE
        }
    }
    
    # Use a port that's less likely to be in use
    port = 15003
    address = f"tcp://127.0.0.1:{port}"
    
    # Start the server in a more isolated way
    server = SQLiteServer(
        bind_address=address,
        database=":memory:",
        auth_config=auth_config
    )
    
    # Start server and wait for it to be ready
    server.start()
    if not wait_for_server("127.0.0.1", port, timeout=5):
        pytest.fail(f"Server failed to start on port {port}")
    
    LOG.info("Started Test SQLiteServer on port %d with PID %d", port, server.pid)
    
    # Create client with configured timeouts
    client = SQLiteClient(
        connect_address=address,
        # Set a shorter timeout for tests
        request_timeout=2000
    )
    
    # Verify client can connect
    try:
        # Try a simple test query with short timeout
        response = client.execute("SELECT 1", retries=1, request_timeout=1000)
        LOG.info("Test connection successful: %s", response)
    except Exception as e:
        LOG.warning("Initial test connection failed: %s", e)
    
    # Yield client
    yield client
    
    # Cleanup
    LOG.info("Cleaning up test resources")
    try:
        client.cleanup()
        LOG.info("Client cleanup completed")
    except Exception as e:
        LOG.error("Error during client cleanup: %s", e)
    
    # Kill server process
    LOG.info("Stopping server (PID %d)", server.pid)
    if platform.system().lower() == 'windows':
        os.system(f"taskkill /F /pid {server.pid}")
    else:
        kill_process(server.pid)
    
    # Wait briefly to ensure process terminates
    time.sleep(0.5)
    
    # Ensure no zombie processes are left
    try:
        server.join(timeout=2)
        LOG.info("Server process joined successfully")
    except Exception as e:
        LOG.error("Error joining server process: %s", e)