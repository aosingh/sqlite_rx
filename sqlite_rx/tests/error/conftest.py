import pytest
import logging.config

from sqlite_rx import get_default_logger_settings
from sqlite_rx.client import SQLiteClient


logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger("error_sqlite_client")


@pytest.fixture(scope="module")
def error_client():
    LOG.info("Initializing SQLite Client")
    client = SQLiteClient(connect_address="tcp://127.0.0.1:5004")
    yield client
    LOG.info("Shutting down SQLite Client")
    client.cleanup()
