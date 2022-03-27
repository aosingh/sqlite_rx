import os
import sys
import platform
import signal
import tempfile
import pytest

import sqlite3
import logging.config

from collections import namedtuple
from sqlite_rx import get_default_logger_settings
from sqlite_rx.backup import is_backup_supported
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger(__file__)

backup_event = namedtuple('backup_event', ('client', 'backup_database', 'main_database'))


@pytest.fixture(scope="module")
def plain_client():

    auth_config = {
        sqlite3.SQLITE_OK: {
            sqlite3.SQLITE_DROP_TABLE
        }
    }
    with tempfile.TemporaryDirectory() as base_dir:

        main_db_file = os.path.join(base_dir, 'main.db')
        backup_db_file = os.path.join(base_dir, 'backup.db')

        if is_backup_supported():
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5003",
                                  database=main_db_file,
                                  auth_config=auth_config,
                                  backup_database=backup_db_file,
                                  backup_interval=1)
        else:
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5003",
                                  database=main_db_file,
                                  auth_config=auth_config)
        
        client = SQLiteClient(connect_address="tcp://127.0.0.1:5003")

        event = backup_event(client=client, backup_database=backup_db_file, main_database=main_db_file)

        server.start()

        LOG.info("Started Test SQLiteServer")

        yield event

        if platform.system().lower() == 'windows':
            os.system("taskkill  /F /pid "+str(server.pid))
        else:
            os.kill(server.pid, signal.SIGINT)

        server.join()
        client.cleanup()