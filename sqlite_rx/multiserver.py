import logging
import os
import signal
import socket
import time
import uuid
import platform
import collections
import re
from typing import Dict, List, Union, Optional, OrderedDict, Callable
from datetime import datetime
from pathlib import Path

import billiard as multiprocessing  # Using billiard for better process management
import msgpack
import zmq
import zlib
from . import get_version
from .auth import KeyMonkey
from .exception import SQLiteRxZAPSetupError
from .server import SQLiteServer
from .monitor import ProcessMonitor
from .utils.path_utils import resolve_database_path

LOG = logging.getLogger(__name__)
try:
    import psutil
except (ImportError, ModuleNotFoundError):
    psutil = None

class DatabaseProcess:
    """Represents a database process with its configuration and control info."""
    
    def __init__(self, 
                 database_name: str,
                 database_path: Union[bytes, str, Path],
                 bind_port: int,
                 auth_config: dict = None,
                 use_encryption: bool = False,
                 use_zap_auth: bool = False,
                 curve_dir: str = None,
                 server_curve_id: str = None,
                 backup_database: Union[str, Path] = None,
                 backup_interval: int = 600,
                 data_directory: Union[str, Path] = None):
        """
        Initialize a database process configuration.
        
        Args:
            database_name: Name of the database for routing
            database_path: Path to the database file
            bind_port: Port on which the database server will listen
            auth_config: Authorization configuration
            use_encryption: Whether to use CurveZMQ encryption
            use_zap_auth: Whether to use ZAP authentication
            curve_dir: Directory containing curve keys
            server_curve_id: Server's curve key ID
            backup_database: Path to backup database
            backup_interval: Backup interval in seconds
            data_directory: Base directory for database files
        """
        self.database_name = database_name
        self.database_path = database_path
        self.bind_port = bind_port
        self.bind_address = f"tcp://127.0.0.1:{bind_port}"
        self.process_id = None
        self.process = None
        self.auth_config = auth_config
        self.use_encryption = use_encryption
        self.use_zap_auth = use_zap_auth
        self.curve_dir = curve_dir
        self.server_curve_id = server_curve_id
        self.backup_database = backup_database
        self.backup_interval = backup_interval
        self.restart_count = 0
        self.start_time = time.time()
        self.last_start_time = None
        self.data_directory = data_directory
        

    def start(self):
        """Start the database process."""
        if self.process and self.process.is_alive():
            LOG.warning(f"Process for database '{self.database_name}' is already running")
            return
            
        # Create a server but DON'T pass 'name' in the constructor
        server = SQLiteServer(
            bind_address=self.bind_address,
            database=self.database_path,
            auth_config=self.auth_config,
            use_encryption=self.use_encryption,
            use_zap_auth=self.use_zap_auth,
            curve_dir=self.curve_dir,
            server_curve_id=self.server_curve_id,
            backup_database=self.backup_database,
            backup_interval=self.backup_interval,
            data_directory=self.data_directory  # Pass data_directory
        )
        
        # Set the name directly instead
        server.name = f"DB-{self.database_name}-{uuid.uuid4().hex[:8]}"
        
        server.start()
        self.process = server
        self.process_id = server.pid
        self.last_start_time = time.time()
        LOG.info(f"Started database process for '{self.database_name}' on {self.bind_address} with PID {self.process_id}")
        
    def stop(self):
        """Stop the database process."""
        if not self.process:
            LOG.warning(f"No process found for database '{self.database_name}'")
            return
            
        if not self.process.is_alive():
            LOG.warning(f"Process for database '{self.database_name}' is not running")
            return
            
        try:
            LOG.info(f"Stopping database process for '{self.database_name}' (PID {self.process_id})")
            os.kill(self.process_id, signal.SIGTERM)
            # Give it some time to clean up
            self.process.join(timeout=5)
            
            # Force kill if still alive
            if self.process.is_alive():
                LOG.warning(f"Process for database '{self.database_name}' did not terminate, forcing...")
                os.kill(self.process_id, signal.SIGKILL)
                self.process.join(timeout=1)
        except Exception as e:
            LOG.error(f"Error stopping database process for '{self.database_name}': {e}")
        
        self.process = None
        self.process_id = None
        
    def is_running(self):
        """Check if the database process is running."""
        return self.process is not None and self.process.is_alive()
        
    def get_uptime(self):
        """Get the uptime of the current process instance."""
        if self.is_running() and self.last_start_time:
            return time.time() - self.last_start_time
        return 0


class SQLiteMultiServer(multiprocessing.Process):
    """A ZeroMQ ROUTER socket server that routes SQLite requests to separate database processes."""

    def __init__(self,
                bind_address: str,
                default_database: Union[bytes, str, Path],
                database_map: Dict[str, Union[bytes, str, Path]] = None,
                auth_config: dict = None,
                curve_dir: str = None,
                server_curve_id: str = None,
                use_encryption: bool = False,
                use_zap_auth: bool = False,
                backup_dir: str = None,
                backup_interval: int = 600,
                base_port: int = 6000,
                data_directory: Union[str, Path] = None,
                auto_connect: bool = False,
                auto_create: bool = False,
                max_connections: int = 20,
                enable_monitoring: bool = True,
                resource_monitoring: bool = True,
                log_directory: str = None,
                notification_callback: Callable = None,
                *args, **kwargs):
        """
        SQLiteMultiServer starts separate processes for each database.

        Args:
            bind_address: The address and port for the router socket
            default_database: Path to the default database
            database_map: Dictionary mapping database names to paths
            auth_config: Authorization configuration
            curve_dir: Directory for curve keys
            server_curve_id: Server's curve ID
            use_encryption: Whether to use encryption
            use_zap_auth: Whether to use ZAP authentication
            backup_dir: Directory for database backups
            backup_interval: Backup interval in seconds
            base_port: Starting port for database processes
            data_directory: Base directory for database files (if relative paths are used)
            auto_connect: Whether to automatically connect to existing databases
            auto_create: Whether to automatically create new databases
            max_connections: Maximum number of dynamic database connections to maintain
            enable_monitoring: Whether to enable process monitoring
            resource_monitoring: Whether to enable resource usage monitoring
            log_directory: Directory to store log files
            notification_callback: Function to call for alerts (takes name, type, message)
        """
        super(SQLiteMultiServer, self).__init__(*args, **kwargs)
        self._bind_address = bind_address
        self._data_directory = data_directory
        
        # Store the original database paths (for passing to child processes)
        self._default_database_orig = default_database
        self._database_map_orig = database_map or {}
        
        # Resolve the database paths for local use
        self._default_database = resolve_database_path(default_database, data_directory)
        self._database_map = {k: resolve_database_path(v, data_directory) 
                            for k, v in (database_map or {}).items()}
        
        self._auth_config = auth_config
        self._encrypt = use_encryption
        self._zap_auth = use_zap_auth
        self.server_curve_id = server_curve_id
        self.curve_dir = curve_dir
        self.backup_dir = backup_dir
        self.backup_interval = backup_interval
        self.base_port = base_port
        
        # Auto-connection settings
        self._auto_connect = auto_connect
        self._auto_create = auto_create
        self._max_connections = max_connections
        
        # Monitoring settings
        self._enable_monitoring = enable_monitoring
        self._resource_monitoring = resource_monitoring
        self._log_directory = log_directory
        self._notification_callback = notification_callback
        
        # Will be initialized in setup()
        self.context = None
        self.router_socket = None
        self.database_processes = {}
        self.identity_db_map = {}
        self.poller = None
        self.running = False
        self.process_monitor = None
        
        # LRU Cache for dynamic database processes
        # OrderedDict naturally maintains insertion order which we'll use for LRU
        self._dynamic_processes = collections.OrderedDict()
        self._next_dynamic_port = None  # Will be set in setup
        
        # Initialize health metrics
        self._start_time = time.time()
        self._health_metrics = {
            "query_count": 0,
            "error_count": 0,
            "last_query_time": 0,
            "total_process_restarts": 0,
            "dynamic_connections_created": 0,
            "dynamic_connections_evicted": 0,
        }
        self.name = kwargs.pop('name', f"SQLiteMultiServer-{os.getpid()}")
        
    def setup_database_processes(self):
        """Set up all database processes."""
        # Start with the default database
        default_backup = None
        if self.backup_dir:
            default_backup = os.path.join(self.backup_dir, "default_backup.db")
                
        default_process = DatabaseProcess(
            database_name="",
            database_path=self._default_database_orig,  # Pass original path
            bind_port=self.base_port,
            auth_config=self._auth_config,
            use_encryption=self._encrypt,
            use_zap_auth=self._zap_auth,
            curve_dir=self.curve_dir,
            server_curve_id=self.server_curve_id,
            backup_database=default_backup,
            backup_interval=self.backup_interval,
            data_directory=self._data_directory  # Pass data_directory
        )
        self.database_processes[""] = default_process
        
        # Keep track of the highest port used
        highest_port = self.base_port
        
        # Now set up each named database
        port = self.base_port + 1
        for db_name, db_path in self._database_map_orig.items():  # Use original paths
            backup_path = None
            if self.backup_dir:
                backup_path = os.path.join(self.backup_dir, f"{db_name}_backup.db")
                    
            db_process = DatabaseProcess(
                database_name=db_name,
                database_path=db_path,  # Pass original path
                bind_port=port,
                auth_config=self._auth_config,
                use_encryption=self._encrypt,
                use_zap_auth=self._zap_auth,
                curve_dir=self.curve_dir,
                server_curve_id=self.server_curve_id,
                backup_database=backup_path,
                backup_interval=self.backup_interval,
                data_directory=self._data_directory  # Pass data_directory
            )
            self.database_processes[db_name] = db_process
            highest_port = port
            port += 1
        
        # Set the next port for dynamic databases
        self._next_dynamic_port = highest_port + 1
            
    def start_database_processes(self):
        """Start all database processes."""
        for db_name, db_process in self.database_processes.items():
            db_process.start()
            
            # Register with process monitor if enabled
            if self.process_monitor:
                self.process_monitor.register_process(
                    f"db-{db_name}" if db_name else "db-default", 
                    db_process.process
                )
            # Give a short delay between process starts to avoid port conflicts
            time.sleep(0.1)
            
        ready = self.wait_for_databases_ready()
        if not ready:
            LOG.error("Failed to start all database processes")
            raise RuntimeError("Failed to start all database processes")

    def wait_for_databases_ready(self, timeout=10):
        """Wait until all database processes are running and responding."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            all_ready = True
            for db_name, db_process in self.database_processes.items():
                if not db_process.is_running():
                    all_ready = False
                    break
            if all_ready:
                return True
            time.sleep(0.1)
        return False
            
    def stop_database_processes(self):
        """Stop all database processes (both static and dynamic)."""
        # Stop static database processes
        for db_name, db_process in self.database_processes.items():
            db_process.stop()
            
        # Stop dynamic database processes
        for db_name, db_process in self._dynamic_processes.items():
            db_process.stop()
            
    def check_database_processes(self):
        """Check if all database processes are running and restart any that died."""
        for db_name, db_process in self.database_processes.items():
            if not db_process.is_running():
                LOG.warning(f"Database process for '{db_name or 'default'}' is not running, restarting...")
                db_process.start()
                # Give it a moment to start up
                time.sleep(0.5)
    
    def setup(self):
        """Set up the ROUTER socket and database connections."""
        LOG.info("Python Platform %s", multiprocessing.current_process().name)
        LOG.info("libzmq version %s", zmq.zmq_version())
        LOG.info("pyzmq version %s", zmq.__version__)
        
        # Create ZeroMQ context
        self.context = zmq.Context()
        
        # Initialize ROUTER socket for client connections
        self.router_socket = self.context.socket(zmq.ROUTER)
        
        if self._encrypt or self._zap_auth:
            server_curve_id = self.server_curve_id if self.server_curve_id else f"id_server_{socket.gethostname()}_curve"
            keymonkey = KeyMonkey(key_id=server_curve_id, destination_dir=self.curve_dir)

            if self._encrypt:
                LOG.info("Setting up encryption using CurveCP")
                self.router_socket = keymonkey.setup_secure_server(self.router_socket, self._bind_address)

            if self._zap_auth:
                if not self._encrypt:
                    raise SQLiteRxZAPSetupError("ZAP requires CurveZMQ(use_encryption = True) to be enabled.")

                LOG.info("ZAP enabled. Authorizing clients in %s.", keymonkey.authorized_clients_dir)
                # Note: ZAP auth would need to be properly implemented here

        self.router_socket.bind(self._bind_address)
        LOG.info(f"ROUTER socket bound to {self._bind_address}")
        
        # Set up polling for incoming messages
        self.poller = zmq.Poller()
        self.poller.register(self.router_socket, zmq.POLLIN)
        
        # Set up dealer sockets to each database process
        self.setup_database_processes()
        
        # Initialize process monitor if enabled
        if self._enable_monitoring:
            from sqlite_rx.monitor import ProcessMonitor
            self.process_monitor = ProcessMonitor(check_interval=30)
            
            # Configure additional monitor settings
            if self._resource_monitoring:
                self.process_monitor.resource_check_interval = 60  # Check resources every minute
            
            if self._log_directory:
                self.process_monitor.log_directory = self._log_directory
                
            if callable(self._notification_callback):
                self.process_monitor.notification_callback = self._notification_callback
                
            # Start the monitoring thread
            self.process_monitor.start_monitoring()
            LOG.info("Process monitor started")
        
        self.start_database_processes()

    def handle_client_request(self, message_parts):
        """Process a client request received on the ROUTER socket."""
        # The first part is the client identity
        identity = message_parts[0]
        
        # In the REQ/REP pattern, there's an empty delimiter frame after the identity
        empty_delimiter = message_parts[1]
        
        # The actual message content is in the last part
        message_data = message_parts[-1]
        
        try:
            # Decompress and unpack the message
            unpacked_message = msgpack.loads(zlib.decompress(message_data), raw=False)
            
            # Extract database name from the message
            database_name = unpacked_message.get("database_name", "")
            
            # Store the mapping between identity and database name for responses
            self.identity_db_map[identity] = database_name
            
            # Check for health check command
            if unpacked_message.get('query') == 'HEALTH_CHECK':
                LOG.debug("Received HEALTH_CHECK request for database %s", database_name or "default")
                
                # Generate health info
                health_info = self.get_health_info(database_name)
                
                # Send health info response
                compressed_result = zlib.compress(msgpack.dumps(health_info))
                self.router_socket.send_multipart([identity, empty_delimiter, compressed_result])
                return
            
            # Update metrics for regular queries
            self._health_metrics["query_count"] += 1
            self._health_metrics["last_query_time"] = time.time()
            
            # Get or create a database process for this request
            db_process = self._get_or_create_database_process(database_name)
            
            if db_process:
                # Check if the process is running
                if not db_process.is_running():
                    LOG.warning(f"Database process for '{database_name or 'default'}' is not running, restarting...")
                    
                    # Try to determine why the process isn't running
                    exit_code = db_process.process.exitcode if hasattr(db_process.process, 'exitcode') else None
                    LOG.info(f"Previous process exit code: {exit_code}")
                    
                    # Start a new process
                    db_process.start()
                    LOG.info(f"Started new process for database '{database_name or 'default'}'")
                    
                    # Update restart metrics
                    self._health_metrics["total_process_restarts"] += 1
                    
                    # Give it time to initialize
                    time.sleep(1.0)  # Increased delay to ensure the process is ready
                    
                    # Verify the process is now running
                    if not db_process.is_running():
                        LOG.error(f"Failed to restart database process for '{database_name or 'default'}'")
                        self._send_error_response(identity, empty_delimiter, 
                                                f"Unable to restart database process for '{database_name}'")
                        
                        # Update error metrics
                        self._health_metrics["error_count"] += 1
                        return
                
                # Forward the request to the database process
                try:
                    # Create a temporary dealer socket to forward the request
                    dealer_socket = self.context.socket(zmq.DEALER)
                    dealer_socket.setsockopt(zmq.LINGER, 0)  # Don't wait for unsent messages
                    dealer_socket.connect(db_process.bind_address)
                    
                    # Forward the message
                    dealer_socket.send_multipart(message_parts[1:])  # Skip the identity
                    
                    # Wait for a response with timeout
                    poller = zmq.Poller()
                    poller.register(dealer_socket, zmq.POLLIN)
                    
                    timeout_ms = 5000  # 5 seconds timeout
                    socks = dict(poller.poll(timeout_ms))
                    
                    if dealer_socket in socks and socks[dealer_socket] == zmq.POLLIN:
                        # Get the response
                        response_parts = dealer_socket.recv_multipart()
                        
                        # Send the response back to the client with the original identity
                        response = [identity] + response_parts
                        self.router_socket.send_multipart(response)
                    else:
                        # Handle timeout
                        LOG.warning(f"Timeout waiting for response from database '{database_name or 'default'}'")
                        self._send_error_response(identity, empty_delimiter, 
                                                f"Timeout waiting for response from database '{database_name}'")
                        
                        # Update error metrics
                        self._health_metrics["error_count"] += 1
                    
                    # Clean up the temporary socket
                    poller.unregister(dealer_socket)
                    dealer_socket.close()
                    
                except Exception as e:
                    LOG.exception(f"Error forwarding request to database '{database_name}': {e}")
                    self._send_error_response(identity, empty_delimiter, 
                                            f"Error communicating with database '{database_name}': {str(e)}")
                    
                    # Update error metrics
                    self._health_metrics["error_count"] += 1
                    
            else:
                # We don't have a process for this database
                LOG.warning(f"Database '{database_name}' not found")
                self._send_error_response(identity, empty_delimiter, f"Database '{database_name}' not found")
                
                # Update error metrics
                self._health_metrics["error_count"] += 1
                
        except Exception as e:
            LOG.exception(f"Error processing client request: {e}")
            self._send_error_response(identity, empty_delimiter, f"Error processing request: {str(e)}")
            
            # Update error metrics
            self._health_metrics["error_count"] += 1
        
    def _get_dynamic_database_path(self, database_name: str) -> Optional[str]:
        """
        Get the path for a dynamic database.
        
        Args:
            database_name: Name of the database
            
        Returns:
            Path to the database file, or None if it doesn't exist or can't be created
        """
        if not database_name or not self._data_directory:
            return None
        
        # Validate database name to prevent potential security issues
        if not self._is_valid_database_name(database_name):
            LOG.warning(f"Invalid database name requested: {database_name}")
            return None
        
        # Construct the path
        db_path = os.path.join(self._data_directory, f"{database_name}.db")
        
        # Check if database exists (for auto_connect)
        if os.path.exists(db_path):
            return db_path
        
        # If it doesn't exist and auto_create is enabled, return the path anyway
        if self._auto_create:
            return db_path
        
        # Otherwise, return None to indicate we can't use this database
        return None

    def _is_valid_database_name(self, database_name: str) -> bool:
        """
        Check if a database name is valid and safe.
        
        Args:
            database_name: The name to check
            
        Returns:
            True if valid, False otherwise
        """
        # Block empty names, names with path separators, or other dangerous characters
        if not database_name or len(database_name) > 64:
            return False
        
        # Only allow alphanumeric chars, underscore, and hyphen
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', database_name))

    def _create_dynamic_database_process(self, database_name: str) -> Optional[DatabaseProcess]:
        """
        Create a new database process for a dynamically requested database.
        
        Args:
            database_name: Name of the database to create
        
        Returns:
            DatabaseProcess instance or None if creation failed
        """
        # Get the database path
        db_path = self._get_dynamic_database_path(database_name)
        if not db_path:
            return None
        
        # Create backup path if needed
        backup_path = None
        if self.backup_dir:
            backup_path = os.path.join(self.backup_dir, f"{database_name}_backup.db")
        
        # Assign a port
        port = self._next_dynamic_port
        self._next_dynamic_port += 1
        
        # Create the process
        db_process = DatabaseProcess(
            database_name=database_name,
            database_path=db_path,
            bind_port=port,
            auth_config=self._auth_config,
            use_encryption=self._encrypt,
            use_zap_auth=self._zap_auth,
            curve_dir=self.curve_dir,
            server_curve_id=self.server_curve_id,
            backup_database=backup_path,
            backup_interval=self.backup_interval,
            data_directory=self._data_directory
        )
        
        try:
            # Start the process
            db_process.start()
            LOG.info(f"Created dynamic database process for '{database_name}' on port {port}")
            
            # Update metrics
            self._health_metrics["dynamic_connections_created"] += 1
            
            return db_process
        except Exception as e:
            LOG.error(f"Failed to create dynamic database process for '{database_name}': {e}")
            return None

    def _get_or_create_database_process(self, database_name: str) -> Optional[DatabaseProcess]:
        """
        Get a database process for the requested database, creating it if necessary.
        
        Args:
            database_name: Name of the database to get or create
            
        Returns:
            DatabaseProcess instance or None if getting/creating failed
        """
        # First check configured databases
        if database_name in self.database_processes:
            return self.database_processes[database_name]
        
        # Return None if auto-connect is disabled
        if not self._auto_connect:
            return None
        
        # Check if we already have a dynamic process for this database
        if database_name in self._dynamic_processes:
            # Move to the end of the OrderedDict to mark as most recently used
            db_process = self._dynamic_processes.pop(database_name)
            self._dynamic_processes[database_name] = db_process
            return db_process
        
        # Otherwise, try to create a new process
        db_process = self._create_dynamic_database_process(database_name)
        if not db_process:
            return None
        
        # If we've reached the connection limit, evict the least recently used database
        if len(self._dynamic_processes) >= self._max_connections:
            # Get the first key (least recently used)
            oldest_db = next(iter(self._dynamic_processes))
            oldest_process = self._dynamic_processes.pop(oldest_db)
            
            # Stop the process
            LOG.info(f"Evicting least recently used database '{oldest_db}' to make room for '{database_name}'")
            oldest_process.stop()
            
            # Update metrics
            self._health_metrics["dynamic_connections_evicted"] += 1
        
        # Add the new process to our cache
        self._dynamic_processes[database_name] = db_process
        return db_process

    def _send_error_response(self, identity, empty_delimiter, error_message):
        """Helper method to send an error response to the client."""
        error = {
            "type": "sqlite_rx.exception.SQLiteRxError",
            "message": error_message
        }
        result = {"items": [], "error": error}
        
        try:
            compressed_result = zlib.compress(msgpack.dumps(result))
            self.router_socket.send_multipart([identity, empty_delimiter, compressed_result])
            LOG.debug(f"Error response sent to client {identity}: {error_message}")
        except Exception as send_error:
            LOG.error(f"Failed to send error response to client: {send_error}")

    def handle_signal(self, signum, frame):
        """Handle termination signals."""
        LOG.info(f"SQLiteMultiServer {self} PID {self.pid} received {signum}")
        LOG.info("SQLiteMultiServer Shutting down")
        
        # Stop all database processes
        self.cleanup()    
        self.running = False
        raise SystemExit()
    
    # Helper functions for metrics calculations
    def _calculate_query_success_rate(self):
        """Calculate the query success rate as a percentage."""
        query_count = self._health_metrics.get("query_count", 0)
        error_count = self._health_metrics.get("error_count", 0)
        
        if query_count == 0:
            return 100.0  # No queries made yet
        
        success_rate = ((query_count - error_count) / query_count) * 100
        return round(success_rate, 2)
    
    def _calculate_query_rate(self):
        """Calculate the average queries per second."""
        query_count = self._health_metrics.get("query_count", 0)
        uptime = time.time() - self._start_time
        
        if uptime < 1:
            return 0.0
        
        return round(query_count / uptime, 2)

    def get_health_info(self, database_name='', check_system_resources=True):
        """
        Generate comprehensive health information for the multi-server.
        
        Args:
            database_name: Optional database name to get specific health info
            check_system_resources: Whether to check system resources
        Returns:
            Dict containing health information
        """
        # Basic health information
        health_info = {
            "status": "healthy",
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self._start_time,
            "version": get_version(),
            "platform": platform.python_implementation(),
            "python_version": platform.python_version(),
            "server_type": "SQLiteMultiServer",
            "server_name": self.name,
            "server_pid": self.pid,
            "database_name": database_name,
        }
        
        # Add query metrics
        health_info["metrics"] = {
            "query_count": self._health_metrics["query_count"],
            "error_count": self._health_metrics["error_count"],
            "last_query_time": self._health_metrics["last_query_time"],
            "query_success_rate": self._calculate_query_success_rate(),
            "queries_per_minute": self._calculate_query_rate() * 60,
            "total_process_restarts": self._health_metrics["total_process_restarts"],
            "dynamic_connections_created": self._health_metrics["dynamic_connections_created"],
            "dynamic_connections_evicted": self._health_metrics["dynamic_connections_evicted"],
        }
        
        # Add connection info
        health_info["connection"] = {
            "auto_connect_enabled": self._auto_connect,
            "auto_create_enabled": self._auto_create,
            "max_connections": self._max_connections,
            "active_dynamic_connections": len(self._dynamic_processes),
            "router_address": self._bind_address,
        }
        
        # Add security info
        health_info["security"] = {
            "encryption_enabled": self._encrypt,
            "zap_auth_enabled": self._zap_auth,
        }
        
        # Add data directory info
        if self._data_directory:
            health_info["data_directory"] = str(self._data_directory)
            health_info["storage"] = {
                "data_directory": str(self._data_directory),
                "backup_directory": str(self.backup_dir) if self.backup_dir else None,
                "backup_interval_seconds": self.backup_interval if self.backup_dir else 0,
            }
            
            # Add storage stats if possible
            if psutil:
                try:
                        if os.path.exists(self._data_directory):
                            disk_usage = psutil.disk_usage(self._data_directory)
                        health_info["storage"].update({
                            "disk_total_gb": round(disk_usage.total / (1024**3), 2),
                            "disk_used_gb": round(disk_usage.used / (1024**3), 2),
                            "disk_free_gb": round(disk_usage.free / (1024**3), 2),
                            "disk_percent_used": disk_usage.percent,
                        })
                except Exception as e:
                    health_info["storage"]["disk_stats_error"] = str(e)
        
        # Add system resource info
        if psutil:
            try:
                # CPU information
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_count = psutil.cpu_count(logical=True)
                cpu_count_physical = psutil.cpu_count(logical=False)
                
                # Memory information
                virtual_mem = psutil.virtual_memory()
                swap_mem = psutil.swap_memory()
                
                health_info["system"] = {
                    "cpu_percent": cpu_percent,
                    "cpu_count": cpu_count,
                    "cpu_count_physical": cpu_count_physical,
                    "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None,
                    "memory_total_mb": round(virtual_mem.total / (1024**2), 2),
                    "memory_available_mb": round(virtual_mem.available / (1024**2), 2),
                    "memory_used_mb": round(virtual_mem.used / (1024**2), 2),
                    "memory_percent": virtual_mem.percent,
                    "swap_total_mb": round(swap_mem.total / (1024**2), 2),
                    "swap_used_mb": round(swap_mem.used / (1024**2), 2),
                    "swap_percent": swap_mem.percent,
                }
                
                # Determine if system resources are constrained
                if check_system_resources and (cpu_percent > 90 or virtual_mem.percent > 90 or swap_mem.percent > 90):
                    health_info["status"] = "constrained"
                    health_info["status_reason"] = "System resources running low"
            except Exception as e:
                health_info["system_stats_error"] = str(e)
        
        # Get info about all static database processes
        processes_info = {}
        for db_name, db_process in self.database_processes.items():
            process_info = {
                "running": db_process.is_running(),
                "pid": db_process.process_id if db_process.process_id else None,
                "port": db_process.bind_port,
                "address": db_process.bind_address,
                "database_name": db_name or "default",
                "type": "static",
                "uptime_seconds": db_process.get_uptime() if db_process.is_running() else 0,
            }
            
            # Add restart count if available
            restart_count = getattr(db_process, 'restart_count', 0)
            process_info["restart_count"] = restart_count
            
            # Add database path
            if hasattr(db_process, 'database_path'):
                process_info["database_path"] = str(db_process.database_path)
                if str(db_process.database_path) == ":memory:":
                    process_info["memory_database"] = True
                else:
                    process_info["memory_database"] = False
                    
                    # Add database size if available
                    try:
                        if os.path.exists(str(db_process.database_path)):
                            size_bytes = os.path.getsize(str(db_process.database_path))
                            process_info["database_size_bytes"] = size_bytes
                            process_info["database_size_mb"] = round(size_bytes / (1024**2), 2)
                    except Exception:
                        pass
            
            # Add backup info
            if hasattr(db_process, 'backup_database') and db_process.backup_database:
                process_info["backup"] = {
                    "enabled": True,
                    "path": str(db_process.backup_database),
                    "interval_seconds": db_process.backup_interval,
                }
                
                # Add backup size if available
                try:
                    if os.path.exists(str(db_process.backup_database)):
                        size_bytes = os.path.getsize(str(db_process.backup_database))
                        process_info["backup"]["size_bytes"] = size_bytes
                        process_info["backup"]["size_mb"] = round(size_bytes / (1024**2), 2)
                        process_info["backup"]["last_modified"] = datetime.fromtimestamp(
                            os.path.getmtime(str(db_process.backup_database))
                        ).isoformat()
                except Exception:
                    pass
            else:
                process_info["backup"] = {"enabled": False}
            
            # If process is not running, mark health status as degraded
            if not db_process.is_running():
                health_info["status"] = "degraded"
                health_info["status_reason"] = f"Database process '{db_name or 'default'}' is not running"
            
            processes_info[db_name or "default"] = process_info
        
        # Also include dynamic database processes
        dynamic_processes_info = {}
        for db_name, db_process in self._dynamic_processes.items():
            process_info = {
                "running": db_process.is_running(),
                "pid": db_process.process_id if db_process.process_id else None,
                "port": db_process.bind_port,
                "address": db_process.bind_address,
                "database_name": db_name,
                "type": "dynamic",
                "uptime_seconds": db_process.get_uptime() if db_process.is_running() else 0,
            }
            
            # Add restart count
            restart_count = getattr(db_process, 'restart_count', 0)
            process_info["restart_count"] = restart_count
            
            # Add database path
            if hasattr(db_process, 'database_path'):
                process_info["database_path"] = str(db_process.database_path)
                if str(db_process.database_path) == ":memory:":
                    process_info["memory_database"] = True
                else:
                    process_info["memory_database"] = False
                    
                    # Add database size if available
                    try:
                        if os.path.exists(str(db_process.database_path)):
                            size_bytes = os.path.getsize(str(db_process.database_path))
                            process_info["database_size_bytes"] = size_bytes
                            process_info["database_size_mb"] = round(size_bytes / (1024**2), 2)
                    except Exception:
                        pass
            
            # Add backup info
            if hasattr(db_process, 'backup_database') and db_process.backup_database:
                process_info["backup"] = {
                    "enabled": True,
                    "path": str(db_process.backup_database),
                    "interval_seconds": db_process.backup_interval,
                }
                
                # Add backup size if available
                try:
                    if os.path.exists(str(db_process.backup_database)):
                        size_bytes = os.path.getsize(str(db_process.backup_database))
                        process_info["backup"]["size_bytes"] = size_bytes
                        process_info["backup"]["size_mb"] = round(size_bytes / (1024**2), 2)
                        process_info["backup"]["last_modified"] = datetime.fromtimestamp(
                            os.path.getmtime(str(db_process.backup_database))
                        ).isoformat()
                except Exception:
                    pass
            else:
                process_info["backup"] = {"enabled": False}
            
            # If process is not running, mark health status as degraded
            if not db_process.is_running():
                health_info["status"] = "degraded"
                health_info["status_reason"] = f"Dynamic database process '{db_name}' is not running"
            
            dynamic_processes_info[db_name] = process_info
        
        health_info["processes"] = processes_info
        health_info["dynamic_databases"] = dynamic_processes_info
        health_info["database_count"] = len(processes_info) + len(dynamic_processes_info)
        
        # If process monitor is active, include its health stats
        if hasattr(self, 'process_monitor') and self.process_monitor:
            try:
                monitor_info = self.process_monitor.get_process_info()
                health_info["monitor"] = {
                    "enabled": True,
                    "uptime_seconds": monitor_info.get("__stats__", {}).get("uptime", 0),
                    "total_restarts": monitor_info.get("__stats__", {}).get("total_restarts", 0),
                    "processes_watched": len(monitor_info) - 1,  # Subtract stats entry
                }
                
                # Check for crashed processes
                crashed_processes = [
                    name for name, info in monitor_info.items() 
                    if name != "__stats__" and info.get("status") == "crash_loop"
                ]
                
                if crashed_processes:
                    health_info["status"] = "degraded"
                    health_info["status_reason"] = f"Processes in crash loop: {', '.join(crashed_processes)}"
                    health_info["monitor"]["crashed_processes"] = crashed_processes
            except Exception as e:
                health_info["monitor"] = {
                    "enabled": True,
                    "error": str(e)
                }
        else:
            health_info["monitor"] = {"enabled": False}
        
        # Specific information about requested database
        if database_name in self.database_processes:
            db_process = self.database_processes[database_name]
            health_info["database_status"] = "running" if db_process.is_running() else "not_running"
            health_info["database_type"] = "static"
            
            # Add more specific info about the requested database
            if db_process.is_running():
                # Add information about this specific database
                health_info["database_bind_address"] = db_process.bind_address
                health_info["database_pid"] = db_process.process_id
                
                # Backup info
                if hasattr(db_process, 'backup_database') and db_process.backup_database:
                    health_info["database_backup_enabled"] = True
                    health_info["database_backup_path"] = str(db_process.backup_database)
                    health_info["database_backup_interval"] = db_process.backup_interval
                else:
                    health_info["database_backup_enabled"] = False
        elif database_name in self._dynamic_processes:
            db_process = self._dynamic_processes[database_name]
            health_info["database_status"] = "running" if db_process.is_running() else "not_running"
            health_info["database_type"] = "dynamic"
            
            # Add more specific info about the requested database
            if db_process.is_running():
                # Add information about this specific database
                health_info["database_bind_address"] = db_process.bind_address
                health_info["database_pid"] = db_process.process_id
                
                # Backup info
                if hasattr(db_process, 'backup_database') and db_process.backup_database:
                    health_info["database_backup_enabled"] = True
                    health_info["database_backup_path"] = str(db_process.backup_database)
                    health_info["database_backup_interval"] = db_process.backup_interval
                else:
                    health_info["database_backup_enabled"] = False
        else:
            if database_name:  # Only mark unknown if a specific database was requested
                health_info["database_status"] = "unknown"
                health_info["database_error"] = f"Database '{database_name}' not found"
            else:
                health_info["database_status"] = "default"
        
        return health_info

    def check_database_processes(self):
        """Check all database processes and restart any that have died."""
        for db_name, db_process in self.database_processes.items():
            if not db_process.is_running():
                LOG.warning(f"Database process for '{db_name or 'default'}' is not running, restarting...")
                
                # Try to determine why the process isn't running
                exit_code = db_process.process.exitcode if hasattr(db_process.process, 'exitcode') else None
                LOG.info(f"Process exit code: {exit_code}")
                
                # Start a new process
                db_process.start()
                LOG.info(f"Started new process for database '{db_name or 'default'}'")
                
                # Update restart metrics
                self._health_metrics["total_process_restarts"] += 1
                if hasattr(db_process, 'restart_count'):
                    db_process.restart_count = getattr(db_process, 'restart_count', 0) + 1
                else:
                    db_process.restart_count = 1
                
                # Give it time to initialize
                time.sleep(0.5)

    def cleanup(self):
        """Clean up resources before shutdown."""
        LOG.info("Cleaning up MultiServer resources")
        
        # Stop the process monitor if running
        if hasattr(self, 'process_monitor') and self.process_monitor:
            try:
                self.process_monitor.stop_monitoring()
                LOG.info("Process monitor stopped")
            except Exception as e:
                LOG.error(f"Error stopping process monitor: {e}")
        
        # Clean up database processes
        self.stop_database_processes()
        
        # Clean up sockets
        if hasattr(self, 'router_socket') and self.router_socket:
            try:
                self.router_socket.close()
                LOG.info("Router socket closed")
            except Exception as e:
                LOG.error(f"Error closing router socket: {e}")
        
        # Clean up ZMQ context
        if hasattr(self, 'context') and self.context:
            try:
                self.context.term()
                LOG.info("ZMQ context terminated")
            except Exception as e:
                LOG.error(f"Error terminating ZMQ context: {e}")

    def run(self):
        """Run the multi-database server."""
        # Set up signal handlers
        LOG.info("Setting up signal handlers")
        signal.signal(signal.SIGTERM, self.handle_signal)
        signal.signal(signal.SIGINT, self.handle_signal)
        
        # Set up sockets and connections
        self.setup()
        
        LOG.info(f"SQLiteMultiServer version {get_version()}")
        LOG.info(f"Ready to accept client connections on {self._bind_address}")

        self.running = True
        process_check_time = time.time()
        
        # Start the main loop
        while self.running:
            try:
                # Poll for events on the router socket
                socks = dict(self.poller.poll(1000))  # 1000ms timeout
                
                # Check for messages on the ROUTER socket (from clients)
                if self.router_socket in socks and socks[self.router_socket] == zmq.POLLIN:
                    message = self.router_socket.recv_multipart()
                    self.handle_client_request(message)
                
                # Periodically check if all database processes are alive (every 30 seconds)
                current_time = time.time()
                if current_time - process_check_time > 30:
                    self.check_database_processes()
                    process_check_time = current_time
                    
            except KeyboardInterrupt:
                LOG.info("Keyboard interrupt received, shutting down")
                break
            except Exception as e:
                LOG.exception(f"Error in main loop: {e}")
                
        # Clean up
        self.handle_signal(signal.SIGTERM, None)

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Set up database paths
    database_map = {
        "users": "users.db",
        "products": "products.db",
        "orders": "orders.db"
    }
    
    # Create and start the multi-process server
    server = SQLiteMultiServer(
        bind_address="tcp://0.0.0.0:5000",
        default_database="default.db",
        database_map=database_map,
        backup_dir="./backups",
        backup_interval=300  # 5 minutes
    )
    
    server.start()
    server.join()