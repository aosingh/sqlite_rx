import os
import platform
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
    
    # server.daemon = True

    client = SQLiteClient(connect_address="tcp://127.0.0.1:5003")

    server.start()
    # server.join()
    LOG.info("Started Test SQLiteServer")
    yield client
    if platform.system().lower() == 'windows':
        os.system("taskkill  /F /pid "+str(server.pid))
    else:
        os.kill(server.pid, signal.SIGINT)
    server.join()
    client.cleanup()
    