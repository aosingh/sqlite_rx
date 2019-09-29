import zmq
import sqlite3
import os
import sys
import zmq.auth

from sqlite_rx.exception import InvalidAuthConfig
from sqlite_rx.utils import setup_logger

LOG = setup_logger(name=__file__)


DEFAULT_AUTH_CONFIG = {
            sqlite3.SQLITE_OK: {
                sqlite3.SQLITE_CREATE_INDEX,
                sqlite3.SQLITE_CREATE_TABLE,
                sqlite3.SQLITE_CREATE_TEMP_INDEX,
                sqlite3.SQLITE_CREATE_TEMP_TABLE,
                sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
                sqlite3.SQLITE_CREATE_TEMP_VIEW,
                sqlite3.SQLITE_CREATE_TRIGGER,
                sqlite3.SQLITE_CREATE_VIEW,
                sqlite3.SQLITE_INSERT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_TRANSACTION,
                sqlite3.SQLITE_UPDATE,
                sqlite3.SQLITE_ATTACH,
                sqlite3.SQLITE_DETACH,
                sqlite3.SQLITE_ALTER_TABLE,
                sqlite3.SQLITE_REINDEX,
                sqlite3.SQLITE_ANALYZE,
                },

            sqlite3.SQLITE_DENY: {
                sqlite3.SQLITE_DELETE,
                sqlite3.SQLITE_DROP_INDEX,
                sqlite3.SQLITE_DROP_TABLE,
                sqlite3.SQLITE_DROP_TEMP_INDEX,
                sqlite3.SQLITE_DROP_TEMP_TABLE,
                sqlite3.SQLITE_DROP_TEMP_TRIGGER,
                sqlite3.SQLITE_DROP_TEMP_VIEW,
                sqlite3.SQLITE_DROP_TRIGGER,
                sqlite3.SQLITE_DROP_VIEW,
            },

            sqlite3.SQLITE_IGNORE: {
                sqlite3.SQLITE_PRAGMA
            }

}


class Authorizer:

    def __init__(self, config: dict = None):
        self.config = config if config else DEFAULT_AUTH_CONFIG
        self.valid_return_values = {sqlite3.SQLITE_IGNORE, sqlite3.SQLITE_OK, sqlite3.SQLITE_DENY}
        if any(k not in self.valid_return_values for k in self.config.keys()):
            raise InvalidAuthConfig("Allowed return values are: "
                                    "sqlite3.SQLITE_OK(0), sqlite3.SQLITE_DENY(1), sqlite3.SQLITE_IGNORE(2)")

    def __call__(self, action, *args, **kwargs):
        for return_val, actions in self.config.items():
            if action in actions:
                return return_val
        return sqlite3.SQLITE_DENY


class KeyGenerator:

    def __init__(self,
                 key_id : str = "id_curve",
                 destination_dir: str = None):
        self.my_id = key_id
        self.curvedir = destination_dir if destination_dir else os.path.join(os.path.expanduser("~"), ".curve")
        self.public_key = os.path.join(self.curvedir, "{}.key".format(self.my_id))
        self.private_key = os.path.join(self.curvedir, "{}.key_secret".format(self.my_id))
        self.authorized_clients_dir = os.path.join(self.curvedir, "authorized_clients")

    def generate(self):
        bogus = False
        for key in [ self.public_key, self.private_key ]:
            if os.path.exists(key):
                print("%s already exists. Aborting." % key)
                bogus = True
                break
        if bogus:
            sys.exit(1)

        if not os.path.exists(self.curvedir):
            os.mkdir(self.curvedir)

        if not os.path.exists(self.authorized_clients_dir):
            os.mkdir(self.authorized_clients_dir)

        os.chmod(self.curvedir, 0o700)
        os.chmod(self.authorized_clients_dir, 0o700)

        server_public_file, server_secret_file = zmq.auth.create_certificates(self.curvedir, self.my_id)
        LOG.info(server_public_file)
        LOG.info(server_secret_file)
        os.chmod(self.public_key, 0o600)
        os.chmod(self.private_key, 0o600)
        LOG.info("Created %s." % self.public_key)
        LOG.info("Created %s." % self.private_key)


class KeyMonkey:

    """
    ~/.ssh

    ~/.curve/id_server_curve.key
    ~/.curve/id_server_curve.key-secret


    """

    def __init__(self,
                 key_id: str = "id_curve",
                 destination_dir: str = None):

        self.my_id = key_id
        self.curvedir = destination_dir if destination_dir else os.path.join(os.path.expanduser("~"), ".curve")
        self.public_key = os.path.join(self.curvedir, "{}.key".format(self.my_id))
        self.private_key = os.path.join(self.curvedir, "{}.key_secret".format(self.my_id))
        self.authorized_clients_dir = os.path.join(self.curvedir, "authorized_clients")

    def setup_secure_server(self, server, bind_address: str):
        try:
              foo, bar = zmq.auth.load_certificate(self.private_key)
              server.curve_publickey = foo
              server.curve_secretkey = bar
              server.curve_server = True
              LOG.info("Secure setup completed using on %s using curve key %s." % (bind_address, self.my_id))
              return server
        except IOError:
            LOG.exception("Couldn't load the private key: %s" % self.private_key)
            raise
        except Exception:
            LOG.exception("Exception while setting up CURVECP")
            raise

    def setup_secure_client(self, client, connect_address, servername):
        try:
            foo, bar = zmq.auth.load_certificate(self.private_key)
            client.curve_publickey = foo
            client.curve_secretkey = bar
        except IOError:
            LOG.exception("Couldn't load the client private key: %s" % self.private_key)
        else:
            try:
                foo, _ = zmq.auth.load_certificate(os.path.join(self.curvedir, f"{servername}.key"))
                client.curve_serverkey = foo
            except IOError:
                LOG.exception("Couldn't load the server public key %s " % os.path.join(self.curvedir, f"{servername}.key"))
            else:
                LOG.info("Client connectin to %s (key %s) using curve key '%s'." % (connect_address, servername, self.my_id))
                return client
