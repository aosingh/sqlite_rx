# Create a new file: sqlite_rx/monitor.py

import logging
import threading
import multiprocessing
import os
import signal
import time
from typing import Dict, List, Callable, Optional

LOG = logging.getLogger(__name__)

try:
    import psutil
except (ImportError, ModuleNotFoundError):
    LOG.warning("psutil package not available. Resource monitoring disabled.")



class ProcessMonitor:
    """
    Monitors and manages SQLite database processes.
    
    Features:
    - Regular health checks
    - Automatic process restart
    - Graceful shutdown
    - Statistics collection
    """
    
    def __init__(self, check_interval: int = 10):
        """
        Initialize the process monitor.
        
        Args:
            check_interval: Interval in seconds between process checks
        """
        self.processes = {}  # Maps process names to (process, start_time, restart_count) tuples
        self.check_interval = check_interval
        self.monitor_thread = None
        self.running = False
        self.stats = {
            "total_restarts": 0,
            "uptime": 0,
            "start_time": time.time()
        }
        
    def register_process(self, name: str, process: multiprocessing.Process):
        """
        Register a process to be monitored.
        
        Args:
            name: Unique name for the process
            process: The multiprocessing.Process instance
        """
        if process.is_alive():
            self.processes[name] = {
                "process": process,
                "start_time": time.time(),
                "restart_count": 0,
                "pid": process.pid
            }
            LOG.info(f"Registered process '{name}' (PID {process.pid}) for monitoring")
        else:
            LOG.warning(f"Cannot register non-running process '{name}'")
    
    def unregister_process(self, name: str):
        """
        Stop monitoring a process.
        
        Args:
            name: The name of the process to unregister
        """
        if name in self.processes:
            LOG.info(f"Unregistered process '{name}' from monitoring")
            del self.processes[name]
    
    def start_monitoring(self):
        """Start the monitoring thread."""
        if self.monitor_thread and self.monitor_thread.is_alive():
            LOG.warning("Monitoring thread is already running")
            return
            
        self.running = True
        # Change from multiprocessing.Process to threading.Thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="SQLiteRx-ProcessMonitor"
        )
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        LOG.info(f"Process monitor started (checking every {self.check_interval} seconds)")
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
            # Remove the kill part since threads can't be killed like processes
            # Just log if it didn't terminate properly
            if self.monitor_thread.is_alive():
                LOG.warning("Monitor thread did not terminate cleanly")
        LOG.info("Process monitor stopped")
    
    def _monitor_resources(self):
        """Monitor resource usage of processes and system health."""
        try:
            import psutil
        except NameError:
            LOG.warning("psutil package not available. Resource monitoring disabled.")
            return
        
        # Get overall system stats
        system_stats = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "timestamp": time.time()
        }
        
        # Store in overall stats
        self.stats["system"] = system_stats
        
        # Check for system-wide issues
        if system_stats["cpu_percent"] > 90:
            LOG.warning(f"System CPU usage is high: {system_stats['cpu_percent']}%")
        if system_stats["memory_percent"] > 90:
            LOG.warning(f"System memory usage is high: {system_stats['memory_percent']}%")
        if system_stats["disk_percent"] > 90:
            LOG.warning(f"System disk usage is high: {system_stats['disk_percent']}%")
        
        # Monitor each process
        for name, info in self.processes.items():
            process = info["process"]
            if process.is_alive():
                try:
                    # Get process resource usage
                    proc = psutil.Process(process.pid)
                    
                    # Calculate metrics with a small interval to get CPU usage
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    memory_info = proc.memory_info()
                    io_counters = proc.io_counters() if hasattr(proc, 'io_counters') else None
                    
                    # Calculate process uptime
                    uptime = time.time() - info.get("start_time", time.time())
                    
                    # Store metrics
                    metrics = {
                        "cpu_percent": cpu_percent,
                        "memory_rss_mb": memory_info.rss / (1024 * 1024),
                        "memory_vms_mb": memory_info.vms / (1024 * 1024),
                        "uptime_seconds": uptime,
                        "num_threads": proc.num_threads(),
                        "timestamp": time.time()
                    }
                    
                    # Add IO metrics if available
                    if io_counters:
                        metrics.update({
                            "io_read_mb": io_counters.read_bytes / (1024 * 1024),
                            "io_write_mb": io_counters.write_bytes / (1024 * 1024)
                        })
                    
                    # Store in process info
                    self.processes[name]["metrics"] = metrics
                    
                    # Check for process-specific issues
                    if cpu_percent > 90:
                        LOG.warning(f"Process '{name}' CPU usage is high: {cpu_percent}%")
                    
                    if metrics["memory_rss_mb"] > 1000:  # 1GB
                        LOG.warning(f"Process '{name}' memory usage is high: {metrics['memory_rss_mb']:.2f} MB")
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception) as e:
                    LOG.error(f"Error monitoring resources for '{name}': {e}")
        
        # Update timestamp
        self.stats["last_resource_check"] = time.time()

    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate process."""
        signal.signal(signal.SIGTERM, lambda signum, frame: setattr(self, 'running', False))
        
        resource_check_interval = getattr(self, 'resource_check_interval', 60)  # Default 60 seconds
        last_resource_check = 0
        
        while self.running:
            try:
                # Always check basic process health
                self._check_processes()
                
                # Check resources periodically (less frequently)
                current_time = time.time()
                if current_time - last_resource_check > resource_check_interval:
                    self._monitor_resources()
                    last_resource_check = current_time
                
                time.sleep(self.check_interval)
            except Exception as e:
                LOG.exception(f"Error in process monitor: {e}")
    
    def _capture_process_logs(self, process_name, pid):
        """Capture recent log output for a process that failed."""
        try:
            import subprocess
            import re
            
            # Get recent log entries for this process if available
            # This assumes logging to syslog, adjust based on your logging setup
            if hasattr(self, 'log_directory') and self.log_directory:
                log_file = os.path.join(self.log_directory, f"{process_name}.log")
                if os.path.exists(log_file):
                    # Get last 10 lines from the log file
                    try:
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            return "Last logs:\n" + "".join(lines[-10:])
                    except Exception as e:
                        return f"Could not read log file: {e}"
            
            # Try to get any output from journal if using systemd
            try:
                output = subprocess.check_output(
                    ["journalctl", "-n", "10", f"_PID={pid}"],
                    stderr=subprocess.STDOUT, 
                    timeout=2,
                    universal_newlines=True
                )
                if output.strip():
                    return "Logs from journal:\n" + output
            except (subprocess.SubprocessError, OSError):
                pass
                
            return "No detailed error information available"
        except Exception as e:
            LOG.exception(f"Error capturing logs for process '{process_name}': {e}")
            return "Error capturing process logs"

    def _check_processes(self):
        """Check all registered processes and restart if needed."""
        for name, info in list(self.processes.items()):
            process = info["process"]
            
            if not process.is_alive():
                # Capture exit code and error details
                exit_code = process.exitcode if hasattr(process, 'exitcode') else None
                error_details = self._capture_process_logs(name, info["pid"])
                
                LOG.warning(f"Process '{name}' (PID {info['pid']}) is not running. "
                        f"Exit code: {exit_code}. {error_details}")
                
                # Store failure information
                self.processes[name]["last_failure"] = {
                    "timestamp": time.time(),
                    "exit_code": exit_code,
                    "error_details": error_details
                }
                
                # Create a new process with the same target and args
                target = process._target
                args = process._args if process._args else ()
                kwargs = process._kwargs if process._kwargs else {}
                
                # Check if we should apply backoff or mark as failed
                if not self._should_restart(name, info):
                    LOG.error(f"Not restarting '{name}' due to crash loop protection")
                    continue
                
                new_process = multiprocessing.Process(
                    target=target,
                    args=args,
                    kwargs=kwargs,
                    name=process.name
                )
                new_process.daemon = process.daemon
                
                # Start the new process
                try:
                    new_process.start()
                    
                    # Update process info
                    self.processes[name] = {
                        "process": new_process,
                        "start_time": time.time(),
                        "restart_count": info["restart_count"] + 1,
                        "pid": new_process.pid,
                        "last_restart_time": time.time(),
                        "failures": info.get("failures", []) + [{
                            "timestamp": time.time(),
                            "exit_code": exit_code
                        }]
                    }
                    
                    # Update statistics
                    self.stats["total_restarts"] += 1
                    
                    LOG.info(f"Process '{name}' restarted with new PID {new_process.pid}")
                except Exception as e:
                    LOG.exception(f"Failed to restart process '{name}': {e}")
                    # Mark the process as failed
                    self.processes[name]["status"] = "failed"
    
    def get_process_info(self, name: str = None):
        """
        Get information about monitored processes.
        
        Args:
            name: Optional name of a specific process
            
        Returns:
            Dict with process information
        """
        if name:
            if name in self.processes:
                info = self.processes[name].copy()
                info["uptime"] = time.time() - info["start_time"]
                return info
            return None
        
        # Return info for all processes
        result = {}
        for name, info in self.processes.items():
            process_info = info.copy()
            process_info["uptime"] = time.time() - info["start_time"]
            result[name] = process_info
        
        # Add overall stats
        self.stats["uptime"] = time.time() - self.stats["start_time"]
        result["__stats__"] = self.stats
        
        return result
    
    def _should_restart(self, name, info):
        """Determine if a process should be restarted based on its history."""
        restart_count = info["restart_count"]
        last_restart = info.get("last_restart_time", 0)
        failures = info.get("failures", [])
        
        # Calculate backoff time based on restart count (e.g., 1s, 2s, 4s, 8s...)
        backoff_time = min(60, 2 ** restart_count)
        
        # If we've restarted too recently, delay
        time_since_restart = time.time() - last_restart
        if time_since_restart < backoff_time:
            delay_time = backoff_time - time_since_restart
            LOG.warning(f"Applying restart backoff for '{name}': waiting {delay_time:.1f}s")
            time.sleep(delay_time)
        
        # Check for crash loop: if we've restarted many times in a short period
        recent_failures = [f for f in failures if time.time() - f["timestamp"] < 300]
        if len(recent_failures) >= 5:  # 5 failures in 5 minutes
            LOG.error(f"Process '{name}' appears to be in a crash loop "
                    f"({len(recent_failures)} restarts in 5 minutes)")
            
            # Store crash loop status
            self.processes[name]["status"] = "crash_loop"
            
            # Consider adding notification here (email, webhook, etc.)
            self._notify_crash_loop(name, recent_failures)
            
            return False
        
        return True

    def _notify_crash_loop(self, process_name, failures):
        """Send notification about crash looping process."""
        try:
            message = f"ALERT: Process '{process_name}' is crash looping\n"
            message += f"Recent failures: {len(failures)}\n"
            
            if hasattr(self, 'notification_callback') and callable(self.notification_callback):
                self.notification_callback(process_name, "crash_loop", message)
                
            # Log to a dedicated alerts log
            LOG.critical(message)
        except Exception as e:
            LOG.error(f"Failed to send crash loop notification: {e}")

    def restart_process(self, name: str):
        """
        Manually restart a process.
        
        Args:
            name: Name of the process to restart
            
        Returns:
            bool: True if successful, False otherwise
        """
        if name not in self.processes:
            LOG.warning(f"Process '{name}' not found")
            return False
            
        info = self.processes[name]
        process = info["process"]
        
        # Reset crash loop status if present
        if info.get("status") == "crash_loop":
            LOG.info(f"Resetting crash loop status for '{name}' due to manual restart")
            info.pop("status", None)
        
        # Terminate the process
        try:
            os.kill(process.pid, signal.SIGTERM)
            process.join(timeout=5)
            
            if process.is_alive():
                os.kill(process.pid, signal.SIGKILL)
                process.join(timeout=1)
        except Exception as e:
            LOG.error(f"Error terminating process '{name}': {e}")
        
        # Create and start a new process
        target = process._target
        args = process._args if process._args else ()
        kwargs = process._kwargs if process._kwargs else {}
        
        new_process = multiprocessing.Process(
            target=target,
            args=args,
            kwargs=kwargs,
            name=process.name
        )
        new_process.daemon = process.daemon
        
        new_process.start()
        
        # Update process info
        self.processes[name] = {
            "process": new_process,
            "start_time": time.time(),
            "restart_count": info["restart_count"] + 1,
            "pid": new_process.pid,
            "last_restart_time": time.time(),
            "failures": info.get("failures", [])
        }
        
        # Update statistics
        self.stats["total_restarts"] += 1
        
        LOG.info(f"Process '{name}' manually restarted with new PID {new_process.pid}")
        return True
