# test_monitor.py
import pytest
import os
import signal
import time
import multiprocessing
from unittest.mock import patch, MagicMock
from sqlite_rx.monitor import ProcessMonitor

class DummyProcess(multiprocessing.Process):
    def __init__(self):
        super().__init__()
        self.exit_event = multiprocessing.Event()
        
    def run(self):
        while not self.exit_event.is_set():
            time.sleep(0.1)

def test_process_monitor_init():
    monitor = ProcessMonitor(check_interval=15)
    assert monitor.check_interval == 15
    assert monitor.processes == {}
    assert not monitor.running
    assert "total_restarts" in monitor.stats
    assert "uptime" in monitor.stats

def test_register_process():
    monitor = ProcessMonitor()
    proc = DummyProcess()
    proc.start()
    try:
        monitor.register_process("test_proc", proc)
        assert "test_proc" in monitor.processes
        assert monitor.processes["test_proc"]["process"] == proc
        assert monitor.processes["test_proc"]["restart_count"] == 0
    finally:
        proc.exit_event.set()
        proc.join(timeout=1)

def test_unregister_process():
    monitor = ProcessMonitor()
    proc = DummyProcess()
    proc.start()
    try:
        monitor.register_process("test_proc", proc)
        monitor.unregister_process("test_proc")
        assert "test_proc" not in monitor.processes
    finally:
        proc.exit_event.set()
        proc.join(timeout=1)

def test_restart_process():
    monitor = ProcessMonitor()
    
    # Create a mock process
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.is_alive.return_value = True
    mock_process._target = lambda: None
    mock_process._args = ()
    mock_process._kwargs = {}
    
    # Add the mock process to the monitor
    monitor.processes = {
        "test_proc": {
            "process": mock_process,
            "start_time": time.time(),
            "restart_count": 0,
            "pid": 12345
        }
    }
    
    # Mock os.kill to avoid actually killing anything
    with patch('os.kill') as mock_kill:
        with patch.object(multiprocessing, 'Process') as mock_process_class:
            mock_new_process = mock_process_class.return_value
            mock_new_process.pid = 54321
            
            # Restart the process
            result = monitor.restart_process("test_proc")
            
            # Verify results
            assert result is True
            # Update the expected signal - implementation uses SIGKILL not SIGTERM
            mock_kill.assert_called_with(12345, signal.SIGKILL)