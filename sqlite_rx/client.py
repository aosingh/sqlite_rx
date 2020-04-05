import logging.config
import os
import socket
import threading
import zlib
from pprint import pformat

import msgpack
import zmq
from sqlite_rx.auth import KeyMonkey
from sqlite_rx.exception import (
    InvalidRequest,
    MissingServerCurveKeyID,
    RequestCompressionError,
    RequestSendError,
    SerializationError,
)


DEFAULT_REQUEST_TIMEOUT = 2500
REQUEST_RETRIES = 5


PARENT_DIR = os.path.dirname(__file__)

LOG = logging.getLogger(__name__)

__all__ = ['SQLiteClient']


class SQLiteClient(threading.local):

    def __init__(self,
                 connect_address: str,
                 use_encryption: bool = False,
                 curve_dir: str = None,
                 client_curve_id: str = None,
                 server_curve_id: str = None,
                 context=None):
        """
        A thin and reliable client to send query execution requests to a remote :class: `sqlite_rx.server.SQLiteServer`

        The SQLiteClient has a single method called execute().

        Args:
            connect_address: The address and port on which the server will listen for client requests.
            use_encryption: True means use `CurveZMQ` encryption. False means don't
            curve_dir: Curve key files directory. Defaults to `~/.curve`
            client_curve_id: Server curve id. Defaults to "id_server_{}_curve".format(socket.gethostname())
            server_curve_id: Client curve id. Defaults to "id_client_{}_curve".format(socket.gethostname())
            context: `zmq.Context`

        """
        self.client_id = "python@{}_{}".format(
            socket.gethostname(), threading.get_ident())
        self._context = context or zmq.Context.instance()
        self._connect_address = connect_address
        self._encrypt = use_encryption
        self.server_curve_id = server_curve_id
        client_curve_id = client_curve_id if client_curve_id else "id_client_{}_curve".format(
            socket.gethostname())
        self._keymonkey = KeyMonkey(client_curve_id, destination_dir=curve_dir)
        self._client = self._init_client()
        self._poller = zmq.Poller()
        self._poller.register(self._client, zmq.POLLIN)

    def _init_client(self):
        LOG.info("Initializing Client")
        client = self._context.socket(zmq.REQ)
        if self._encrypt:
            if not self.server_curve_id:
                raise MissingServerCurveKeyID(
                    "Please provide the name of the server key_id to be used for Curve")
            client = self._keymonkey.setup_secure_client(
                client, self._connect_address, self.server_curve_id)
        client.connect(self._connect_address)
        LOG.info("client %s connected successfully" % self.client_id)
        return client

    def execute(self,
                query: str,
                *args,
                **kwargs) -> dict:
        """
        Send the `query` and the parameters to a remote SQLiteServer instance which will then
        execute the query.

        Important keyword arguments are as follows:

            1. `execute_many`: True if you want to insert multiple rows with one execute call.

            2. `execute_script`: True if you want to execute a script with multiple SQL commands.

            3. `request_timeout`: Time in ms to wait for a response before retrying. Default is 2500 ms

            4. `retries`: Number of times to retry before abandoning the request. Default is 5

        Args:
            query: A valid SQL query or SQL script

        Returns:
            response: A dictionary of the form
            {
                "items": []
                "error": None
            }

        Raises:
            sqlite_rx.exception.RequestSendError: An error at the Transport layer i.e. zmq socket
            sqlite_rx.exception.RequestCompressionError: An error while compressing the request body using `zlib`
            sqlite_rx.exception.SerializationError: An error while serializing the request body using `msgpack`

        """
        LOG.info("Executing query %s for client %s" % (query, self.client_id))

        request_retries = kwargs.pop('retries', REQUEST_RETRIES)
        execute_many = kwargs.pop('execute_many', False)
        execute_script = kwargs.pop('execute_script', False)
        request_timeout = kwargs.pop(
            'request_timeout', DEFAULT_REQUEST_TIMEOUT)

        # Do some client side validations.
        if execute_script and execute_many:
            raise InvalidRequest(
                "Both `execute_script` and `execute_many` cannot be True")

        request = {
            "client_id": self.client_id,
            "query": query,
            "params": args,
            "execute_many": execute_many,
            "execute_script": execute_script
        }

        expect_reply = True

        while request_retries:
            LOG.info("Preparing to send request")
            try:
                self._client.send(zlib.compress(msgpack.dumps(request)))
            except zmq.ZMQError:
                LOG.exception("Exception while sending message")
                raise RequestSendError("Transport Error")
            except zlib.error:
                LOG.exception("Exception while request body compression")
                raise RequestCompressionError("zlib compression error")
            except Exception:
                LOG.exception("Exception while serializing the request")
                raise SerializationError("request could not be serialized")

            while expect_reply:
                socks = dict(self._poller.poll(request_timeout))
                if socks.get(self._client) == zmq.POLLIN:
                    response = msgpack.loads(
                        zlib.decompress(
                            self._client.recv()), raw=False)
                    if response and isinstance(response, dict):
                        LOG.debug("Response %s" % pformat(response))
                        return response
                else:
                    LOG.warning(
                        "No response from server, Client will disconnect and retry..")
                    self.shutdown()
                    request_retries -= 1
                    if request_retries == 0:
                        LOG.error("Server seems to be offline, abandoning")
                        break
                    LOG.info("Reconnecting and resending request %r" % request)
                    self._client = self._init_client()
                    self._poller.register(self._client, zmq.POLLIN)

    def shutdown(self):
        self._client.setsockopt(zmq.LINGER, 0)
        self._client.close()
        self._poller.unregister(self._client)
