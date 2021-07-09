import pytest

import os
import platform
import socket
import shutil
import signal
import sqlite3
import logging.config

from sqlite_rx import get_default_logger_settings
from sqlite_rx.auth import KeyGenerator
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer
from sqlite_rx.tests import get_server_auth_files

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger(__file__)


@pytest.fixture(scope="module")
def curvezmq_client():
    with get_server_auth_files() as auth_files:
        curve_dir, server_key_id, server_public_key, server_private_key = auth_files
        client_key_id = "id_client_{}_curve".format(socket.gethostname())
        key_generator = KeyGenerator(destination_dir=curve_dir, key_id=client_key_id)
        key_generator.generate()
        client_public_key = os.path.join(curve_dir, "{}.key".format(client_key_id))
        client_private_key = os.path.join(curve_dir, "{}.key_secret".format(client_key_id))
        shutil.copyfile(client_public_key, os.path.join(curve_dir,
                                                        'authorized_clients',
                                                        "{}.key".format(client_key_id)))
        auth_config = {
            sqlite3.SQLITE_OK: {
                sqlite3.SQLITE_DROP_TABLE
            }
        }
        server = SQLiteServer(bind_address="tcp://127.0.0.1:5002",
                              use_encryption=True,
                              curve_dir=curve_dir,
                              server_curve_id=server_key_id,
                              auth_config=auth_config,
                              database=":memory:")

        # server.daemon = True

        client = SQLiteClient(connect_address="tcp://127.0.0.1:5002",
                              server_curve_id=server_key_id,
                              client_curve_id=client_key_id,
                              curve_dir=curve_dir,
                              use_encryption=True)
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

