# SQLite-RX Health Check API

The Health Check API provides an easy way to monitor the health and status of SQLite-RX servers. This feature is available for both single-server `SQLiteServer` and multi-database `SQLiteMultiServer` deployments.

## Using the Health Check API

The health check is implemented as a special SQL command that can be executed using any SQLite-RX client:

```python
from sqlite_rx.client import SQLiteClient

# Connect to a server
client = SQLiteClient(connect_address="tcp://127.0.0.1:5000")

# Get health information
health_info = client.execute("HEALTH_CHECK")

# Print health status
print(f"Server status: {health_info['status']}")
print(f"Uptime: {health_info['uptime']} seconds")
print(f"Version: {health_info['version']}")
```

## Health Check Response

The health check returns a JSON/dict response with detailed information about the server's status. The response includes:

### Common Fields (Both Server Types)

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Server status ("healthy" or "error") |
| `timestamp` | number | Current server timestamp |
| `uptime` | number | Server uptime in seconds |
| `version` | string | SQLite-RX version |
| `platform` | string | Python implementation (e.g., "CPython") |
| `query_count` | number | Total number of queries processed |
| `error_count` | number | Total number of errors encountered |
| `last_query_time` | number | Timestamp of the last query processed |
| `database_status` | string | Database connection status |
| `memory_database` | boolean | Whether the database is in-memory |

### Single-Server Fields

| Field | Type | Description |
|-------|------|-------------|
| `server_name` | string | Name of the server instance |
| `server_pid` | number | Process ID of the server |
| `backup_enabled` | boolean | Whether database backup is enabled |
| `backup_thread_alive` | boolean | Whether the backup thread is running |
| `backup_interval` | number | Backup interval in seconds |
| `database_path` | string | Path to the database file (if not in-memory) |

### Multi-Server Fields

| Field | Type | Description |
|-------|------|-------------|
| `server_type` | string | Server type ("SQLiteMultiServer") |
| `server_name` | string | Name of the multi-server instance |
| `server_pid` | number | Process ID of the multi-server |
| `database_name` | string | Name of the database queried |
| `database_count` | number | Total number of databases managed |
| `processes` | object | Map of database processes and their status |
| `total_process_restarts` | number | Total number of process restarts |

The `processes` object contains information about each database process:

```json
"processes": {
  "default": {
    "running": true,
    "pid": 12345,
    "port": 6000,
    "address": "tcp://127.0.0.1:6000",
    "restart_count": 0,
    "database_path": "/path/to/default.db",
    "memory_database": false
  },
  "users": {
    "running": true,
    "pid": 12346,
    "port": 6001,
    "address": "tcp://127.0.0.1:6001",
    "restart_count": 1,
    "database_path": "/path/to/users.db",
    "memory_database": false
  }
}
```

## Example: Monitoring Service Health

You can use the health check API to build monitoring tools:

```python
import time
from sqlite_rx.client import SQLiteClient

def monitor_health(address, interval=60):
    """Monitor server health at regular intervals."""
    client = SQLiteClient(connect_address=address)
    
    try:
        while True:
            try:
                health = client.execute("HEALTH_CHECK")
                
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Health Check:")
                print(f"  Status: {health['status']}")
                print(f"  Uptime: {health['uptime'] / 3600:.2f} hours")
                print(f"  Queries: {health['query_count']}")
                print(f"  Errors: {health['error_count']}")
                
                if health['status'] != "healthy":
                    print(f"  WARNING: Server health is {health['status']}")
                    
                # For multi-server, check process status
                if "processes" in health:
                    for db_name, process in health["processes"].items():
                        if not process["running"]:
                            print(f"  WARNING: Database '{db_name}' process is not running!")
                
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERROR: Cannot connect to server: {e}")
                
            time.sleep(interval)
    finally:
        client.cleanup()

# Example usage
if __name__ == "__main__":
    monitor_health("tcp://localhost:5000")
```

## Integration with Monitoring Tools

The health check API can be used to integrate SQLite-RX with standard monitoring solutions:

1. **Prometheus/Grafana**: Create an exporter script that gets health metrics and exposes them to Prometheus
2. **Kubernetes**: Use an HTTP wrapper around the health check for liveness and readiness probes
3. **Docker**: Build health check scripts for container health monitoring
4. **Datadog/NewRelic**: Forward health metrics to APM platforms using their respective agents

## Performance Considerations

The health check is designed to be lightweight, with minimal impact on server performance. It can be called frequently (e.g., every 15-30 seconds) for active monitoring without significant overhead.