import os

import socket

import tempfile
from contextlib import contextmanager
import logging.config

from sqlite_rx import get_default_logger_settings
from sqlite_rx.auth import KeyGenerator

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

LOG = logging.getLogger(__file__)


@contextmanager
def get_server_auth_files():
    """Generate Temporary Private and Public keys for ZAP and CurveZMQ SQLiteServer

    """
    with tempfile.TemporaryDirectory() as curve_dir:
        LOG.info("Curve dir is %s", curve_dir)
        server_key_id = "id_server_{}_curve".format(socket.gethostname())
        key_generator = KeyGenerator(destination_dir=curve_dir, key_id=server_key_id)
        key_generator.generate()
        server_public_key = os.path.join(curve_dir, "{}.key".format(server_key_id))
        server_private_key = os.path.join(curve_dir, "{}.key_secret".format(server_key_id))
        yield curve_dir, server_key_id, server_public_key, server_private_key
