import logging
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

# Try to import psutil for system metrics
try:
    import psutil
except (ImportError, ModuleNotFoundError):
    pass

from .version import get_version
from .monitor import ProcessMonitor

LOG = logging.getLogger(__name__)

__all__ = ['MetricsExporter']

class MetricsExporter:
    """Export metrics to external monitoring systems like Prometheus."""
    
    def __init__(self, monitor, multiserver=None, port=8000, path='/metrics'):
        """
        Initialize the metrics exporter.
        
        Args:
            monitor: ProcessMonitor instance
            multiserver: Optional SQLiteMultiServer instance
            port: HTTP port to expose metrics on
            path: URL path for metrics endpoint
        """
        self.monitor = monitor
        self.multiserver = multiserver
        self.port = port
        self.path = path
        self.server = None
        self.thread = None
        self.running = False
        
    def start(self):
        """Start metrics HTTP server."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import threading
        
        # Define handler using a closure to access self
        metrics_exporter = self  # Reference to use in the handler
        
        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == metrics_exporter.path:
                    metrics = metrics_exporter.get_metrics_text()
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(metrics.encode())
                elif self.path == '/health':
                    health = metrics_exporter.get_health_text()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(health.encode())
                else:
                    self.send_response(404)
                    self.end_headers()
                    self.wfile.write(b'Not Found')
            
            def log_message(self, format, *args):
                # Redirect logs to our logger
                LOG.debug(f"MetricsServer: {format % args}")
        
        # Create and start the server in a separate thread
        try:
            self.server = HTTPServer(('', self.port), MetricsHandler)
            self.thread = threading.Thread(target=self._serve_forever)
            self.thread.daemon = True
            self.running = True
            self.thread.start()
            LOG.info(f"Metrics server started on port {self.port}")
            return True
        except Exception as e:
            LOG.error(f"Failed to start metrics server: {e}")
            return False
    
    def _serve_forever(self):
        """Server main loop, wrapped to handle clean shutdown."""
        try:
            self.server.serve_forever()
        except Exception as e:
            if self.running:  # Only log if not shutting down intentionally
                LOG.error(f"Metrics server error: {e}")
    
    def stop(self):
        """Stop the metrics server."""
        self.running = False
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
                LOG.info("Metrics server stopped")
            except Exception as e:
                LOG.error(f"Error stopping metrics server: {e}")
        
        if self.thread and self.thread.is_alive():
            try:
                self.thread.join(timeout=5)
                if self.thread.is_alive():
                    LOG.warning("Metrics server thread did not terminate cleanly")
            except Exception as e:
                LOG.error(f"Error joining metrics server thread: {e}")
    
    def get_metrics_text(self):
        """Format metrics in Prometheus text format."""
        lines = []
        timestamp_ms = int(time.time() * 1000)
        
        # Add server info
        lines.append(f"# TYPE sqlite_rx_server_info gauge")
        lines.append(f'sqlite_rx_server_info{{version="{get_version()}"}} 1 {timestamp_ms}')
        
        # Add uptime metric
        if self.monitor:
            uptime = time.time() - self.monitor.stats.get("start_time", time.time())
            lines.append(f"# TYPE sqlite_rx_uptime_seconds gauge")
            lines.append(f"sqlite_rx_uptime_seconds {uptime} {timestamp_ms}")
        
        # Add process metrics from the monitor
        if self.monitor:
            info = self.monitor.get_process_info()
            
            # Process count
            process_count = len([p for p in info.keys() if p != "__stats__"])
            lines.append(f"# TYPE sqlite_rx_process_count gauge")
            lines.append(f"sqlite_rx_process_count {process_count} {timestamp_ms}")
            
            # Restart count
            total_restarts = info.get("__stats__", {}).get("total_restarts", 0)
            lines.append(f"# TYPE sqlite_rx_total_restarts counter")
            lines.append(f"sqlite_rx_total_restarts {total_restarts} {timestamp_ms}")
            
            # Process metrics
            lines.append(f"# TYPE sqlite_rx_process_uptime_seconds gauge")
            lines.append(f"# TYPE sqlite_rx_process_restart_count counter")
            lines.append(f"# TYPE sqlite_rx_process_running gauge")
            lines.append(f"# TYPE sqlite_rx_process_cpu_percent gauge")
            lines.append(f"# TYPE sqlite_rx_process_memory_mb gauge")
            
            for name, process_info in info.items():
                if name == "__stats__":
                    continue
                    
                uptime = process_info.get("uptime", 0)
                restart_count = process_info.get("restart_count", 0)
                running = 1 if process_info.get("running", False) else 0
                
                lines.append(f'sqlite_rx_process_uptime_seconds{{name="{name}"}} {uptime} {timestamp_ms}')
                lines.append(f'sqlite_rx_process_restart_count{{name="{name}"}} {restart_count} {timestamp_ms}')
                lines.append(f'sqlite_rx_process_running{{name="{name}"}} {running} {timestamp_ms}')
                
                # Add resource metrics if available
                metrics = process_info.get("metrics", {})
                if metrics:
                    cpu_percent = metrics.get("cpu_percent", 0)
                    memory_mb = metrics.get("memory_rss_mb", 0)
                    
                    lines.append(f'sqlite_rx_process_cpu_percent{{name="{name}"}} {cpu_percent} {timestamp_ms}')
                    lines.append(f'sqlite_rx_process_memory_mb{{name="{name}"}} {memory_mb} {timestamp_ms}')
        
        # Add multiserver metrics if available
        if self.multiserver:
            # Query metrics
            lines.append(f"# TYPE sqlite_rx_query_count counter")
            lines.append(f"sqlite_rx_query_count {self.multiserver._health_metrics.get('query_count', 0)} {timestamp_ms}")
            
            lines.append(f"# TYPE sqlite_rx_error_count counter")
            lines.append(f"sqlite_rx_error_count {self.multiserver._health_metrics.get('error_count', 0)} {timestamp_ms}")
            
            # Database metrics
            lines.append(f"# TYPE sqlite_rx_database_count gauge")
            lines.append(f"sqlite_rx_database_count {len(self.multiserver.database_processes)} {timestamp_ms}")
            
            lines.append(f"# TYPE sqlite_rx_dynamic_database_count gauge")
            lines.append(f"sqlite_rx_dynamic_database_count {len(self.multiserver._dynamic_processes)} {timestamp_ms}")
        
        # Add system metrics if available
        try:
            import psutil
            
            # CPU usage
            lines.append(f"# TYPE sqlite_rx_system_cpu_percent gauge")
            lines.append(f"sqlite_rx_system_cpu_percent {psutil.cpu_percent(interval=0.1)} {timestamp_ms}")
            
            # Memory usage
            mem = psutil.virtual_memory()
            lines.append(f"# TYPE sqlite_rx_system_memory_percent gauge")
            lines.append(f"sqlite_rx_system_memory_percent {mem.percent} {timestamp_ms}")
            
            lines.append(f"# TYPE sqlite_rx_system_memory_available_mb gauge")
            lines.append(f"sqlite_rx_system_memory_available_mb {mem.available / (1024*1024)} {timestamp_ms}")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            lines.append(f"# TYPE sqlite_rx_system_disk_percent gauge")
            lines.append(f"sqlite_rx_system_disk_percent {disk.percent} {timestamp_ms}")
            
        except (ImportError, Exception) as e:
            lines.append(f"# System metrics unavailable: {str(e)}")
        
        return '\n'.join(lines)
    
    def get_health_text(self):
        """Generate a health check response in JSON format."""
        import json
        
        health = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": get_version()
        }
        
        # Add monitor info
        if self.monitor:
            monitor_info = self.monitor.get_process_info()
            failed_processes = []
            
            for name, info in monitor_info.items():
                if name == "__stats__":
                    continue
                
                if info.get("status") == "failed" or info.get("status") == "crash_loop":
                    failed_processes.append({
                        "name": name,
                        "status": info.get("status"),
                        "restart_count": info.get("restart_count", 0),
                        "last_failure": info.get("last_failure", {})
                    })
            
            if failed_processes:
                health["status"] = "degraded"
                health["failed_processes"] = failed_processes
        
        # Add multiserver info
        if self.multiserver:
            health["query_count"] = self.multiserver._health_metrics.get("query_count", 0)
            health["error_count"] = self.multiserver._health_metrics.get("error_count", 0)
            health["database_count"] = len(self.multiserver.database_processes)
            health["dynamic_database_count"] = len(self.multiserver._dynamic_processes)
        
        return json.dumps(health)