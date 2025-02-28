import pytest

import os
import platform
import socket
import shutil
import sqlite3
import logging.config

from sqlite_rx import get_default_logger_settings
from sqlite_rx.auth import KeyGenerator
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer
from sqlite_rx.tests import get_server_auth_files


logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger(__file__)

import signal

@pytest.fixture(scope='module')
def zap_client():
    # Move the entire functionality inside the with block
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
            sqlite3.SQLITE_OK : {
                sqlite3.SQLITE_DROP_TABLE
            }
        }
        
        server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                            use_zap_auth=True,
                            use_encryption=True,
                            curve_dir=curve_dir,
                            server_curve_id=server_key_id,
                            auth_config=auth_config,
                            database=":memory:")

        client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                            server_curve_id=server_key_id,
                            client_curve_id=client_key_id,
                            curve_dir=curve_dir,
                            use_encryption=True)
        
        server.start()
        LOG.info("Started Test SQLiteServer")
        
        try:
            yield client
        finally:
            LOG.info("Cleaning up ZAP test resources")
            
            # First clean up the client
            try:
                client.cleanup()
                LOG.info("Client cleanup completed")
            except Exception as e:
                LOG.error(f"Error during client cleanup: {e}")
            
            # Now properly shut down the server
            if platform.system().lower() == 'windows':
                try:
                    os.system(f"taskkill /F /pid {server.pid}")
                    LOG.info(f"Sent taskkill to server PID {server.pid}")
                except Exception as e:
                    LOG.error(f"Error using taskkill on server: {e}")
            else:
                try:
                    # First try SIGTERM for graceful shutdown
                    os.kill(server.pid, signal.SIGTERM)
                    LOG.info(f"Sent SIGTERM to server PID {server.pid}")
                    
                    # Give it a short time to shut down
                    time.sleep(1)
                    
                    # Check if it's still running
                    try:
                        os.kill(server.pid, 0)  # Signal 0 just checks if process exists
                        LOG.warning(f"Server still running after SIGTERM, sending SIGKILL")
                        os.kill(server.pid, signal.SIGKILL)
                    except OSError:
                        # Process already gone, which is good
                        LOG.info("Server successfully terminated")
                except Exception as e:
                    LOG.error(f"Error killing server: {e}")
            
            # Wait for server to join (with timeout)
            try:
                server.join(timeout=5)
                LOG.info("Server process joined")
            except Exception as e:
                LOG.warning(f"Error joining server process: {e}")

