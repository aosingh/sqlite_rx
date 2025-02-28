import logging.config
import os
import socket
import threading
import zlib
import time

import msgpack
import zmq
from .auth import KeyMonkey
from .exception import (
    SQLiteRxCompressionError,
    SQLiteRxConnectionError,
    SQLiteRxTransportError,
    SQLiteRxSerializationError,
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
                database_name: str = '', 
                context=None,
                **kwargs):
        """
        A thin and reliable client to send query execution requests to a remote SQLiteServer or SQLiteMultiServer

        The SQLiteClient has a single method called execute().

        Args:
            connect_address: The address and port on which the server will listen for client requests.
            use_encryption: True means use `CurveZMQ` encryption. False means don't
            curve_dir: Curve key files directory. Defaults to `~/.curve`
            client_curve_id: Server curve id. Defaults to "id_server_{}_curve".format(socket.gethostname())
            server_curve_id: Client curve id. Defaults to "id_client_{}_curve".format(socket.gethostname())
            database_name: The name of the database to use. Empty string means use the default database.
            context: `zmq.Context`

        """
        self.client_id = "python@{}_{}".format(socket.gethostname(), threading.get_ident())
        self._context = context or zmq.Context.instance()
        self._connect_address = connect_address
        self._encrypt = use_encryption
        self.server_curve_id = server_curve_id if server_curve_id else "id_server_{}_curve".format(socket.gethostname())
        client_curve_id = client_curve_id if client_curve_id else "id_client_{}_curve".format(socket.gethostname())
        self._keymonkey = KeyMonkey(client_curve_id, destination_dir=curve_dir)
        self._database_name = database_name
        self._client = self._init_client()
        # Track if we created our own context
        self._own_context = context is None
        self._context = context or zmq.Context.instance()

    def _init_client(self):
        """Initialize and configure the ZMQ client socket."""
        LOG.info("Initializing Client")
        if self._database_name:
            LOG.info("Using database %s", self._database_name)
        
        # Create a new socket
        try:
            client = self._context.socket(zmq.REQ)
            
            # Configure socket
            client.setsockopt(zmq.LINGER, 0)  # Don't wait on close
            client.setsockopt(zmq.RCVTIMEO, 5000)  # 5 second receive timeout
            client.setsockopt(zmq.SNDTIMEO, 5000)  # 5 second send timeout
            
            # Setup encryption if requested
            if self._encrypt:
                LOG.debug("requests will be encrypted; will load CurveZMQ keys")
                client = self._keymonkey.setup_secure_client(client, self._connect_address, self.server_curve_id)
            
            # Connect to server
            client.connect(self._connect_address)
            
            # Setup poller
            poller = zmq.Poller()
            poller.register(client, zmq.POLLIN)
            self._poller = poller
            
            LOG.info("registered zmq poller")
            LOG.info("client %s initialisation completed", self.client_id)
            return client
        except Exception as e:
            LOG.exception("Error initializing client socket: %s", e)
            # Clean up if initialization fails
            if 'client' in locals():
                try:
                    client.close()
                except:
                    pass
            raise

    def _send_request(self, request):
        try:
            self._client.send(zlib.compress(msgpack.dumps(request)))
        except zmq.ZMQError:
            LOG.exception("Exception while sending message")
            raise SQLiteRxTransportError("ZMQ send error")
        except zlib.error:
            LOG.exception("Exception while request body compression")
            raise SQLiteRxCompressionError("zlib compression error")
        except Exception:
            LOG.exception("Exception while serializing the request")
            raise SQLiteRxSerializationError("msgpack serialization")

    def _recv_response(self):
        try:
            response = msgpack.loads(zlib.decompress(self._client.recv()), raw=False)
        except zmq.ZMQError:
            LOG.exception("Exception while receiving message")
            raise SQLiteRxTransportError("ZMQ receive error")
        except zlib.error:
            LOG.exception("Exception while request body decompression")
            raise SQLiteRxCompressionError("zlib compression error")
        except Exception:
            LOG.exception("Exception while deserializing the request")
            raise SQLiteRxSerializationError("msgpack deserialization error")
        return response

    def execute(self, query: str, *args, **kwargs) -> dict:
        """
        Send a query to a SQLite server and get the response.
        
        Improved to handle socket errors better and ensure proper cleanup.
        """
        LOG.info("Executing query %s for client %s", query, self.client_id)

        request_retries = kwargs.pop('retries', REQUEST_RETRIES)
        execute_many = kwargs.pop('execute_many', False)
        execute_script = kwargs.pop('execute_script', False)
        request_timeout = kwargs.pop('request_timeout', DEFAULT_REQUEST_TIMEOUT)

        # Client side validations
        if execute_script and execute_many:
            raise ValueError("Both `execute_script` and `execute_many` cannot be True")

        # Prepare request data
        request = {
            "client_id": self.client_id,
            "query": query,
            "params": args[0] if len(args) == 1 and isinstance(args[0], tuple) else args,  # Handle single parameter tuple correctly
            "execute_many": execute_many,
            "execute_script": execute_script,
        }
        if self._database_name:
            request["database_name"] = self._database_name

        # Send request with retries
        response = None
        last_error = None
        
        for attempt in range(request_retries):
            # Ensure we have a valid socket
            if self._client is None:
                LOG.info("Initializing new client socket (attempt %d)", attempt + 1)
                try:
                    self._client = self._init_client()
                except Exception as e:
                    LOG.error("Failed to initialize client socket: %s", e)
                    time.sleep(0.5)  # Brief delay before retry
                    continue
            
            try:
                # Send the request
                LOG.info("Sending request (attempt %d)", attempt + 1)
                self._send_request(request)
                
                # Wait for response
                start_time = time.time()
                while time.time() - start_time < request_timeout / 1000:  # Convert ms to seconds
                    try:
                        socks = dict(self._poller.poll(100))  # Poll in shorter intervals
                        if socks.get(self._client) == zmq.POLLIN:
                            response = self._recv_response()
                            return response
                    except zmq.ZMQError as e:
                        LOG.error("ZMQ error while polling: %s", e)
                        break
                        
                # If we got here, timeout occurred
                LOG.warning("No response from server, retrying...")
                
            except SQLiteRxTransportError as e:
                # Socket error - need to recreate
                LOG.error("Transport error: %s", e)
                last_error = e
            except Exception as e:
                LOG.exception("Unexpected error during execute: %s", e)
                last_error = e
                
            # Clean up and prepare for retry
            self.cleanup()
            time.sleep(0.5)  # Brief delay before retry
        
        # If we get here, all retries failed
        LOG.error("Server seems to be offline, abandoning after %d attempts", request_retries)
        if last_error:
            raise SQLiteRxConnectionError(f"No response after retrying: {last_error}")
        else:
            raise SQLiteRxConnectionError("No response after retrying. Abandoning Request")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def cleanup(self):
        """Clean up ZMQ resources properly."""
        try:
            # First unregister from poller to prevent poll on closed socket
            if hasattr(self, '_poller') and self._poller and hasattr(self, '_client'):
                try:
                    self._poller.unregister(self._client)
                    LOG.debug("Unregistered socket from poller")
                except zmq.ZMQError as e:
                    if e.errno != zmq.ENOTSOCK:  # Only log non-expected errors
                        LOG.warning("Error unregistering from poller: %s", e)
                
            # Then close the socket
            if hasattr(self, '_client') and self._client:
                try:
                    self._client.setsockopt(zmq.LINGER, 0)  # Don't wait for unsent messages
                    self._client.close()
                    LOG.debug("Closed client socket")
                except zmq.ZMQError as e:
                    if e.errno in (zmq.EINVAL, zmq.EPROTONOSUPPORT, zmq.ENOCOMPATPROTO, 
                                zmq.EADDRINUSE, zmq.EADDRNOTAVAIL):
                        LOG.error("ZeroMQ Transportation endpoint was not setup")
                    elif e.errno in (zmq.ENOTSOCK,):
                        LOG.error("ZeroMQ request was made against a non-existent device or invalid socket")
                    elif e.errno in (zmq.ETERM, zmq.EMTHREAD,):
                        LOG.error("ZeroMQ context is not a state to handle this request for socket")
                    else:
                        LOG.error("Unexpected ZMQ error during cleanup: %s", e)
        except Exception as e:
            LOG.exception("Exception during client cleanup: %s", e)
        
                # Then clean up context if we own it
        if self._own_context and hasattr(self, '_context') and self._context:
            try:
                # Only terminate if not the default context
                if id(self._context) != id(zmq.Context.instance()):
                    self._context.term()
                LOG.debug("ZMQ context terminated")
            except Exception as e:
                LOG.warning("Error terminating ZMQ context: %s", e)
        # Set socket to None to prevent reuse
        self._client = None
