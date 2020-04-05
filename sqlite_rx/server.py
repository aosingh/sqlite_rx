import logging.config
import multiprocessing
import os
import socket
import sqlite3
import sys
import traceback
import zlib
from pprint import pformat
from typing import List, Union, Callable

import msgpack
import zmq
from sqlite_rx import get_default_logger_settings
from sqlite_rx.auth import Authorizer, KeyMonkey
from sqlite_rx.exception import ZAPSetupError
from tornado import ioloop
from zmq.auth.ioloop import IOLoopAuthenticator
from zmq.eventloop import zmqstream


PARENT_DIR = os.path.dirname(__file__)

LOG = logging.getLogger(__name__)

__all__ = ['SQLiteServer']


class SQLiteZMQProcess(multiprocessing.Process):

    def __init__(self, *args, **kwargs):
        """The :class: ``sqlite_rx.server.SQLiteServer`` is intended to run as an isolated process.
        This class represents some of the abstractions for isolated server process

        """
        self.context = None
        self.loop = None
        self.socket = None
        self.auth = None
        super(SQLiteZMQProcess, self).__init__(*args, **kwargs)

    @staticmethod
    def info(message):
        LOG.info(message)

    @staticmethod
    def debug(message):
        LOG.debug(message)

    @staticmethod
    def log_exception(message):
        LOG.exception(message)

    def setup(self):
        """Creates a ZMQ `context` and a Tornado `eventloop` for the SQLiteServer process
        """
        self.context = zmq.Context()
        self.loop = ioloop.IOLoop.instance()

    def stream(self,
               sock_type,
               address: str,
               callback: Callable = None,
               use_encryption: bool = False,
               server_curve_id: str = None,
               curve_dir: str = None,
               use_zap: bool = False):
        """

        Method used to setup a ZMQ stream which will be bound to a ZMQ.REP socket.
        On this REP stream we register a callback to execute client queries as they arrive.
        The stream is used in conjunction with `tornado` eventloop

        Args:
            sock_type: ZMQ Socket type. For e.g. zmq.REP
            address: Address to bind to
            callback: A callback to invoke as messages arrive on the ZMQ stream
            use_encryption: True if you want CurveZMQ encryption to be enabled
            server_curve_id: Server curve id. Defaults to "id_server_{}_curve".format(socket.gethostname())
            curve_dir: Curve key files directory. Defaults to `~/.curve`
            use_zap: True if you want ZAP authentication to be enabled.

        Raises:
            sqlite_rx.exception.ZAPSetupError: If ZAP is enabled without CurveZMQ
        """

        self.socket = self.context.socket(sock_type)

        if use_encryption or use_zap:

            server_curve_id = server_curve_id if server_curve_id else "id_server_{}_curve".format(
                socket.gethostname())
            keymonkey = KeyMonkey(
                key_id=server_curve_id,
                destination_dir=curve_dir)

            if use_encryption:
                self.info("Setting up encryption using CurveCP")
                self.socket = keymonkey.setup_secure_server(
                    self.socket, address)

            if use_zap:
                if not use_encryption:
                    raise ZAPSetupError(
                        "ZAP requires CurveZMQ(use_encryption = True) to be enabled. Exiting")

                self.auth = IOLoopAuthenticator(self.context)
                # self.auth.deny([])
                self.info(
                    "ZAP enabled. \n Authorizing clients in %s." %
                    keymonkey.authorized_clients_dir)
                self.auth.configure_curve(
                    domain="*", location=keymonkey.authorized_clients_dir)
                self.auth.start()

        self.socket.bind(address)

        stream = zmqstream.ZMQStream(self.socket, self.loop)
        if callback:
            stream.on_recv(callback)
        return stream


class SQLiteServer(SQLiteZMQProcess):

    def __init__(self,
                 bind_address: str,
                 database: Union[bytes, str],
                 auth_config: dict = None,
                 curve_dir: str = None,
                 server_curve_id: str = None,
                 use_encryption: bool = False,
                 use_zap_auth: bool = False,
                 *args, **kwargs):
        """
        SQLiteServer runs as an isolated python process.

        Args:
            bind_address : The address and port on which the server will listen for client requests.
            database: A path like object or the string ":memory:" for in-memory database.
            context: The ZMQ context
            auth_config : A dictionary describing what actions are authorized, denied or ignored.
            use_encryption : True means use `CurveZMQ` encryption. False means don't
            use_zap_auth : True means use `ZAP` authentication. False means don't

        """
        self._bind_address = bind_address
        self._database = database
        self._auth_config = auth_config
        self._encrypt = use_encryption
        self._zap_auth = use_zap_auth
        self.server_curve_id = server_curve_id
        self.curve_dir = curve_dir
        self.rep_stream = None
        super(SQLiteServer, self).__init__(*args, *kwargs)

    def setup(self):
        """
        Start a zmq.REP socket stream and register a callback :class: `sqlite_rx.server.QueryStreamHandler`

        """
        super().setup()

        # Depending on the initialization parameters either get a plain stream or secure stream.
        self.rep_stream = self.stream(zmq.REP,
                                      self._bind_address,
                                      use_encryption=self._encrypt,
                                      use_zap=self._zap_auth,
                                      server_curve_id=self.server_curve_id,
                                      curve_dir=self.curve_dir)
        # Register the callback.
        self.rep_stream.on_recv(QueryStreamHandler(self.rep_stream,
                                                   self._database,
                                                   self._auth_config))

    def run(self):
        self.setup()
        self.info("Server Event Loop started")
        self.loop.start()

    def stop(self):
        self.loop.stop()
        self.socket.close()


class QueryStreamHandler:

    def __init__(self,
                 rep_stream,
                 database: Union[bytes, str],
                 auth_config: dict = None):
        """
        Executes SQL queries and send results back on the `zmq.REP` stream

        Args:
             rep_stream: The zmq.REP socket stream on which to send replies.
             database: A path like object or the string ":memory:" for in-memory database.
             auth_config: A dictionary describing what actions are authorized, denied or ignored.

        """
        self._connection = sqlite3.connect(database=database,
                                           isolation_level=None,
                                           check_same_thread=False)
        self._connection.execute('pragma journal_mode=wal')
        self._connection.set_authorizer(Authorizer(config=auth_config))
        self._cursor = self._connection.cursor()
        self._rep_stream = rep_stream

    @staticmethod
    def capture_exception():
        exc_type, exc_value, exc_tb = sys.exc_info()
        exc_type_string = "%s.%s" % (exc_type.__module__, exc_type.__name__)
        error = {"type": exc_type_string, "message": traceback.format_exception_only(
            exc_type, exc_value)[-1].strip()}
        return error

    def __call__(self, message: List):
        try:
            message = message[-1]
            message = msgpack.loads(zlib.decompress(message), raw=False)
            self._rep_stream.send(self.execute(message))
        except Exception:
            LOG.exception("exception while preparing response")
            error = self.capture_exception()
            result = {"items": [],
                      "error": error}
            self._rep_stream.send(zlib.compress(msgpack.dumps(result)))

    def execute(self, message: dict, *args, **kwargs):
        LOG.debug("Request received is %s" % pformat(message))
        execute_many = message['execute_many']
        execute_script = message['execute_script']
        error = None
        try:
            if execute_script:
                LOG.debug("sqlite remote execute: execute_script")
                self._cursor.executescript(message['query'])
            elif execute_many and message['params']:
                LOG.debug("sqlite remote execute: execute_many")
                self._cursor.executemany(message['query'], message['params'])
            elif message['params']:
                LOG.debug("sqlite remote execute: execute(with params)")
                self._cursor.execute(message['query'], message['params'])
            else:
                LOG.debug("sqlite remote execute: execute(without params)")
                self._cursor.execute(message['query'])
        except Exception:
            LOG.exception(
                "Exception while executing query %s" %
                message['query'])
            error = self.capture_exception()

        result = {
            "items": [],
            "error": error
        }
        if self._cursor.rowcount > -1:
            result['row_count'] = self._cursor.rowcount

        if error:
            return zlib.compress(msgpack.dumps(result))

        try:
            for row in self._cursor.fetchall():
                result['items'].append(row)
            return zlib.compress(msgpack.dumps(result))
        except Exception:
            LOG.exception("Exception while collecting rows")
            result['error'] = self.capture_exception()
            return zlib.compress(msgpack.dumps(result))
