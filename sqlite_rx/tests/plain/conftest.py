import os
import signal
import pytest

import sqlite3
import logging.config

from sqlite_rx import get_default_logger_settings
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger(__file__)


@pytest.fixture(scope="module")
def plain_client():
    auth_config = {
        sqlite3.SQLITE_OK: {
            sqlite3.SQLITE_DROP_TABLE
        }
    }
    server = SQLiteServer(bind_address="tcp://127.0.0.1:5003",
                          database=":memory:",
                          auth_config=auth_config)

    client = SQLiteClient(connect_address="tcp://127.0.0.1:5003")

    server.start()
    LOG.info("Started Test SQLiteServer")
    yield client
    os.kill(server.pid, signal.SIGINT)
    server.join()
    client.shutdown()
