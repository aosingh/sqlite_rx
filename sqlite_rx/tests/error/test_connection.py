import pytest

from sqlite_rx.exception import SQLiteRxConnectionError


def test_client_connection_error(error_client):
    retries = 2
    timeout_ms = 1
    with pytest.raises(SQLiteRxConnectionError):
        error_client.execute("SELECT * FROM IDOLS", retries=retries, request_timeout=timeout_ms)
