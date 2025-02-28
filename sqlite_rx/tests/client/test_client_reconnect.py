# test_client_reconnect.py
import pytest
from unittest.mock import patch, MagicMock
import zmq
import time
from sqlite_rx.client import SQLiteClient
from sqlite_rx.exception import SQLiteRxConnectionError, SQLiteRxTransportError

def test_client_retry_logic():
    # Create a client with mocked dependencies
    with patch('sqlite_rx.client.zmq.Context'):
        client = SQLiteClient(connect_address="tcp://127.0.0.1:9999")
        
        # Completely replace the socket and poller
        client._client = MagicMock()
        client._poller = MagicMock()
        
        # Override internal methods that try to communicate
        with patch.object(client, '_send_request'):
            with patch.object(client, '_recv_response'):
                # Set up polling to always return no results (timeout)
                client._poller.poll.return_value = {}
                
                # Mock time functions to ensure we exit loops
                with patch('time.time') as mock_time:
                    # First call starts timer, second call is after timeout
                    mock_time.side_effect = [0, 10]  # 10 seconds > timeout/1000
                    
                    # Prevent actual sleeps
                    with patch('time.sleep'):
                        # Execute with minimal retries
                        with pytest.raises(SQLiteRxConnectionError):
                            client.execute("SELECT 1", retries=2, request_timeout=100)
                        
                        # Just verify _send_request was called the right number of times
                        assert client._send_request.call_count == 2

def test_client_transport_error():
    # Test handling of transport errors
    client = SQLiteClient(connect_address="tcp://127.0.0.1:9999")
    
    # Mock socket and poller
    mock_socket = MagicMock()
    client._client = mock_socket
    
    # Mock send_request to raise transport error
    with patch.object(client, '_send_request', side_effect=SQLiteRxTransportError("ZMQ error")):
        # Set a shorter retry for testing
        request_retries = 2
        
        # Should raise exception after all retries
        with pytest.raises(SQLiteRxConnectionError):
            client.execute("SELECT 1", retries=request_retries)