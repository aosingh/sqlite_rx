import sys
import zmq
import zlib
import msgpack
import sqlite3
import socket
import traceback
import multiprocessing

from typing import Union, List

from tornado import ioloop

from zmq.eventloop import zmqstream
from zmq.auth.ioloop import IOLoopAuthenticator

from sqlite_rx.utils import setup_logger
from sqlite_rx.auth import KeyMonkey
from sqlite_rx.auth import Authorizer
from sqlite_rx.exception import ZAPSetupError


LOG = setup_logger(name=__file__)


class SQLiteZMQProcess(multiprocessing.Process):
    """
    This is the base class for all processes and offers utility functions
    for setup and creating new streams
    """

    def __init__(self, *args, **kwargs):
        self.context = None
        self.loop = None
        self.socket = None
        self.logger = setup_logger("zmqprocess")
        super(SQLiteZMQProcess, self).__init__(*args, **kwargs)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def log_exception(self, message):
        self.logger.exception(message)

    def setup(self):
        """
        Creates a `context` and an event `loop` for the process
        :return:
        """
        self.info("ZMQProcess Super method")
        self.context = zmq.Context()
        self.loop = ioloop.IOLoop.instance()
        self.info("Event Loop is %s" % self.loop)

    def stream(self,
               sock_type,
               address,
               callback=None,
               use_encryption: bool = False,
               server_curve_id = None,
               curve_dir = None,
               use_zap: bool = False):

        self.socket = self.context.socket(sock_type)

        if use_encryption or use_zap:

            server_curve_id = server_curve_id if server_curve_id else "id_server_{}_curve".format(socket.gethostname())
            keymonkey = KeyMonkey(key_id=server_curve_id, destination_dir=curve_dir)

            if use_encryption:
                self.info("Setting up encryption using CurveCP")
                self.socket = keymonkey.setup_secure_server(self.socket, address)

            if use_zap:
                if not use_encryption:
                    raise ZAPSetupError("ZAP requires CurveZMQ(use_encryption = True) to be enabled. Exiting")

                self.auth = IOLoopAuthenticator(self.context)
                #self.auth.deny([])
                LOG.info("ZAP enabled. \n Authorizing clients in %s." % keymonkey.authorized_clients_dir)
                self.auth.configure_curve(domain="*", location=keymonkey.authorized_clients_dir)
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
        Description:
            Initialization sequence to start an SQLite Server.

        Params:
            bind_address (str): The address and port on which the server will listen for client requests.
            database: A path like object or the string ":memory:" for in-memory database.
            context: The ZMQ context
            auth_config (dict): A dictionary describing what actions are authorized, denied or ignored.
            use_encryption (bool): True means use `curveZMQ`. False means don't
            use_zap_auth (bool): True means use `ZAP`. False means don't

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
        super().setup()
        # GET A SECURE STREAM OR A NORMAL PLAIN STREAM
        self.rep_stream = self.stream(zmq.REP,
                                      self._bind_address,
                                      use_encryption=self._encrypt,
                                      use_zap=self._zap_auth,
                                      server_curve_id=self.server_curve_id,
                                      curve_dir=self.curve_dir)
        self.rep_stream.on_recv(QueryStreamHandler(self.rep_stream,
                                                   self._database,
                                                   self._auth_config))

    def run(self):
        self.info("Going to start the server")
        self.setup()
        self.loop.start()
        self.info("Event Loop is %s" % self.loop)
        self.info("Server Event Loop started")

    def stop(self):
        self.loop.stop()
        self.socket.close()


class QueryStreamHandler:

    def __init__(self,
                 rep_stream,
                 database: Union[bytes, str],
                 auth_config: dict = None):
        self._connection = sqlite3.connect(database=database,
                                           isolation_level=None,
                                           check_same_thread=False)
        self._connection.execute('pragma journal_mode=wal')
        self._connection.set_authorizer(Authorizer(config=auth_config))
        self._cursor = self._connection.cursor()
        self._rep_stream = rep_stream
        self._logger = setup_logger("query_stream_handler")

    @staticmethod
    def capture_exception():
        exc_type, exc_value, exc_tb = sys.exc_info()
        exc_type_string = "%s.%s" % (exc_type.__module__, exc_type.__name__)
        error = {"type": exc_type_string,
                 "message": traceback.format_exception_only(exc_type, exc_value)[-1].strip()}
        LOG.info("Returning error object")
        return error

    def __call__(self, message: List):
        message = message[-1]
        message = msgpack.loads(zlib.decompress(message), raw=False)
        self._rep_stream.send(self.execute(message))

    def execute(self, message: dict, *args, **kwargs):
        self._logger.debug("message is %r" % message)
        execute_many = message['execute_many']
        execute_script = message['execute_script']

        error = None
        try:
            if execute_script:
                self._logger.debug("sqlite remote execute: execute_script")
                self._cursor.executescript(message['query'])
            elif execute_many and message['params']:
                self._logger.debug("sqlite remote execute: execute_many")
                self._cursor.executemany(message['query'], message['params'])
            elif message['params']:
                self._logger.debug("sqlite remote execute: execute(with params)")
                self._cursor.execute(message['query'], message['params'])
            else:
                self._logger.debug("sqlite remote execute: execute(without params)")
                self._cursor.execute(message['query'])
            self._logger.debug("Row count is %s " % self._cursor.rowcount)
        except Exception:
            self._logger.exception("Exception while executing query %s" % message['query'])
            error = self.capture_exception()

        result = {
            "items": [],
            "error": error
        }
        if self._cursor.rowcount > -1:
            result['row_count'] = self._cursor.rowcount

        if error:
            return zlib.compress(msgpack.dumps(result))

        row = self._cursor.fetchone()
        if row is None:
            return zlib.compress(msgpack.dumps(result))

        try:
            for row in self._cursor.fetchall():
                result['items'].append(row)
            return zlib.compress(msgpack.dumps(result))
        except:
            self._logger.exception("Exception while collecting rows")
            result['error'] = self.capture_exception()
            return zlib.compress(msgpack.dumps(result))



