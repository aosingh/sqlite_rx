# Dynamic Database Auto-Connection

SQLite-RX's MultiServer now supports dynamic database connections, allowing it to automatically connect to existing databases or create new ones on demand, based on client requests.

## Overview

The auto-connection feature enables SQLiteMultiServer to dynamically create and manage database connections beyond those explicitly configured at startup. This provides several benefits:

- **On-Demand Database Creation**: Create databases as needed without server restarts
- **Flexible Multi-Tenant Deployments**: Support multiple user databases without pre-configuration
- **Resource Management**: Control the maximum number of active connections
- **LRU Caching**: Automatically manage database lifecycle with least-recently-used eviction

## Configuration Options

The auto-connection feature introduces three new configuration parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `auto_connect` | Boolean | `False` | Enable automatic connection to existing databases |
| `auto_create` | Boolean | `False` | Enable automatic creation of new databases |
| `max_connections` | Integer | 20 | Maximum number of dynamic database connections |

## How It Works

When a client requests a connection to a database:

1. The server first checks if it's a statically configured database (in `database_map`)
2. If not found and `auto_connect` is enabled, it checks if the database exists in the data directory
3. If found, it creates a new SQLiteServer process for that database
4. If not found and `auto_create` is enabled, it creates a new database file and starts a process
5. The database process is added to an LRU cache that tracks usage
6. When the cache reaches `max_connections`, the least recently used database is evicted

## Usage Examples

### Basic Usage

Start a server with auto-connection enabled:

```bash
sqlite-multiprocess-server \
  --tcp-address tcp://0.0.0.0:5000 \
  --data-directory /var/data/sqlite_rx \
  --auto-connect \
  --auto-create \
  --max-connections 10
```

Connect from a client to a dynamic database:

```python
from sqlite_rx.client import SQLiteClient

# Connect to a database that will be auto-created if it doesn't exist
client = SQLiteClient(
    connect_address="tcp://localhost:5000",
    database_name="user123"  # Will create user123.db if it doesn't exist
)

# Create tables and use the database
client.execute("CREATE TABLE user_data (id INTEGER PRIMARY KEY, data TEXT)")
client.execute("INSERT INTO user_data (data) VALUES (?)", ("Example data",))
```

### Auto-Connect Without Auto-Create

If you want to allow connections to existing databases but not create new ones:

```bash
sqlite-multiprocess-server \
  --tcp-address tcp://0.0.0.0:5000 \
  --data-directory /var/data/sqlite_rx \
  --auto-connect \
  --no-auto-create
```

### Monitoring Dynamic Connections

The health check API provides information about dynamic connections:

```python
health_info = client.execute("HEALTH_CHECK")

# Get count of active dynamic connections
active_count = health_info["active_dynamic_connections"]

# Get details about each dynamic database
dynamic_dbs = health_info["dynamic_databases"]
for db_name, db_info in dynamic_dbs.items():
    print(f"Database: {db_name}, Status: {db_info['running']}")
```

## Database Naming and Security

For security reasons, dynamic database names must follow these rules:

- Only alphanumeric characters, underscores, and hyphens are allowed
- Maximum length is 64 characters
- Names with path separators or other special characters are rejected

This prevents potential path traversal attacks and ensures database names map cleanly to filenames.

## LRU Eviction Policy

When the number of dynamic connections reaches the `max_connections` limit, the server evicts the least recently used connection:

1. Each time a database is accessed, it moves to the end of the LRU queue
2. When a new connection is needed and the cache is full, the oldest (first) entry is removed
3. The process for the evicted database is gracefully terminated
4. If the evicted database is requested again later, it will be reconnected automatically

## Performance Considerations

- Setting `max_connections` too high can lead to excessive memory usage
- Setting it too low can cause thrashing if frequently used databases are constantly evicted
- Each dynamic database runs in its own process, with the associated overhead
- Database startup takes time, so the first query to a database may be slower

## Best Practices

1. **Set Appropriate Limits**: Choose a `max_connections` value that balances resource usage with your access patterns
2. **Use Data Directory**: Always specify a `data_directory` when using auto-connection features
3. **Consider Security**: Enable `auto_create` only when needed, as it allows clients to create new databases
4. **Monitor Usage**: Use the health check API to track database creation and eviction metrics
5. **Pre-Configure Common Databases**: Use the standard `database_map` for frequently accessed databases to prevent them from being evicted

## Example Deployment Scenarios

### Multi-Tenant System

For a multi-tenant system where each user gets their own database:

```python
server = SQLiteMultiServer(
    bind_address="tcp://0.0.0.0:5000",
    default_database="system.db",  # System-wide database
    database_map={},               # No pre-configured user databases
    data_directory="/var/data/tenants",
    auto_connect=True,
    auto_create=True,
    max_connections=50
)
```

### Development Environment

For a development environment with auto-creation for convenience:

```python
server = SQLiteMultiServer(
    bind_address="tcp://127.0.0.1:5000",
    default_database=":memory:",
    data_directory="./dev_data",
    auto_connect=True,
    auto_create=True,
    max_connections=5
)
```

### Production System with Controlled Access

For a production system that allows connection to existing databases but not creation of new ones:

```python
server = SQLiteMultiServer(
    bind_address="tcp://0.0.0.0:5000",
    default_database="/var/data/main.db",
    database_map={
        "users": "/var/data/users.db",
        "products": "/var/data/products.db"
    },
    data_directory="/var/data/dynamic",
    auto_connect=True,
    auto_create=False,
    max_connections=20
)
```
