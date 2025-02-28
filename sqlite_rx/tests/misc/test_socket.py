import pytest
from sqlite_rx.client import SQLiteClient
from sqlite_rx.exception import SQLiteRxConnectionError

def test_client_socket_cleanup():
    """Test that client sockets are properly cleaned up."""
    # Using a port that definitely doesn't have a server
    client = SQLiteClient(connect_address="tcp://127.0.0.1:9999")
    
    try:
        # Force a connection error with minimal retries and timeout
        with pytest.raises(SQLiteRxConnectionError):
            client.execute("SELECT 1", retries=1, request_timeout=100)
        
        # Cleanup should not raise exceptions
        client.cleanup()
        
        # Create a new client and verify it can be cleaned up too
        client2 = SQLiteClient(connect_address="tcp://127.0.0.1:9999")
        client2.cleanup()
        
        # Test context manager
        with SQLiteClient(connect_address="tcp://127.0.0.1:9999") as client3:
            # Just verify the context manager works
            pass
            
    finally:
        # Final cleanup
        client.cleanup()