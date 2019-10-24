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
logging.config.fileConfig(
    os.path.join(
        PARENT_DIR,
        "logging.conf"),
    disable_existing_loggers=False)

LOG = logging.getLogger(__name__)


class SQLiteClient(threading.local):
    """
    A thin & reliable SQLLite Client implemented using ZeroMQ REQ socket and Lazy pirate pattern.

    """

    def __init__(self,
                 connect_address: str,
                 use_encryption: bool = False,
                 curve_dir: str = None,
                 client_curve_id: str = None,
                 server_curve_id: str = None,
                 context=None):
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

    def execute(self, query, *args, **kwargs):
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
