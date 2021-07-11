# sqlite_rx 
[![PyPI version](https://badge.fury.io/py/sqlite-rx.svg)](https://pypi.python.org/pypi/sqlite-rx) [![sqlite-rx](https://github.com/aosingh/sqlite_rx/actions/workflows/sqlite_build.yaml/badge.svg)](https://github.com/aosingh/sqlite_rx/actions) [![Downloads](https://pepy.tech/badge/sqlite-rx)](https://pepy.tech/project/sqlite-rx)


[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)]((https://www.python.org/downloads/release/python-370/)) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)]((https://www.python.org/downloads/release/python-390/))
[![PyPy3.6](https://img.shields.io/badge/python-PyPy3.6-blue.svg)](https://www.pypy.org/index.html)

## Background

[SQLite](https://www.sqlite.org/index.html) is a lightweight database written in C. 
The Python programming language has in-built support to interact with the database (locally) which is either stored on disk or in memory.

## Introduction
With `sqlite_rx`, clients should be able to communicate with an `SQLiteServer` in a fast, simple and secure manner and execute queries remotely.

Key Features

- Python Client and Server for [SQLite](https://www.sqlite.org/index.html) database built using [ZeroMQ](http://zguide.zeromq.org/page:all) as the transport layer and [msgpack](https://msgpack.org/index.html) for serialization/deserialization.
- Authentication using [ZeroMQ Authentication Protocol (ZAP)](https://rfc.zeromq.org/spec:27/ZAP/)
- Encryption using [CurveZMQ](http://curvezmq.org/)
- Generic authorization policy during server startup
- Schedule regular backups for on-disk database (Currently not supported on Windows and for Python versions < 3.7)


# Install

```commandline
pip install sqlite_rx
```

## Supported OS 
- Linux
- MacOS
- Windows

## Supported Python Platforms
- CPython 3.6, 3.7, 3.8, 3.9
- PyPy3.6

## Server

`SQLiteServer` runs in a single thread and follows an event-driven concurrency model (using `tornado's` event loop) which minimizes the cost of concurrent client connections. Following snippet shows how you can start the server process.

```python
from sqlite_rx.server import SQLiteServer

def main():

    # database is a path-like object giving the pathname 
    # of the database file to be opened. 
    
    # You can use ":memory:" to open a database connection to a database 
    # that resides in RAM instead of on disk

    server = SQLiteServer(database=":memory:",
                          bind_address="tcp://127.0.0.1:5000")
    server.start()
    server.join()

if __name__ == '__main__':
    main()

```

## Client

`SQLiteClient` is a thin client with a single method called `execute`

The `execute` method reacts to the following keyword arguments:

1. `execute_many`: True if you want to insert multiple rows with one execute call.

2. `execute_script`: True if you want to execute a script with multiple SQL commands.

3. `request_timeout`: Time in ms to wait for a response before retrying. Default is 2500 ms

4. `retries`: Number of times to retry before abandoning the request. Default is 5


### Instantiate a client

The following snippet shows how you can instantiate an `SQLiteClient` and execute a simple `CREATE TABLE` query.

```python
from sqlite_rx.client import SQLiteClient

client = SQLiteClient(connect_address="tcp://127.0.0.1:5000")

with client:
  query = "CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)"
  result = client.execute(query)

```

```python
{'error': None, 
 'items': []}
```

### INSERT MANY rows

```python
purchases = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
             ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
             ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
             ('2006-04-06', 'SELL', 'XOM', 500, 53.00)]

result = client.execute("INSERT INTO stocks VALUES (?,?,?,?,?)", 
                        *purchases, 
                        execute_many=True)

```

```python
{'error': None, 
 'items': [], 
 'rowcount': 27}
```

### SELECT with WHERE clause

```python
args = ('IBM',)
result = client.execute("SELECT * FROM stocks WHERE symbol = ?", *args)

```

```python
{'error': None,
 'items': [['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0]],
 'lastrowid': 27}

```

### Execute an SQL script

```python
script = '''CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, phone TEXT);
            CREATE TABLE accounts(id INTEGER PRIMARY KEY, description TEXT);

            INSERT INTO users(name, phone) VALUES ('John', '5557241'), 
             ('Adam', '5547874'), ('Jack', '5484522');'''

result = client.execute(script, execute_script=True)

```

```python
{'error': None, 
 'items': [], 
 'lastrowid': 27}
```

Select rows inserted using the above SQL script

```python
result = client.execute("SELECT * FROM users")
```

```python
{'error': None,
 'items': [[1, 'John', '5557241'],
           [2, 'Adam', '5547874'],
           [3, 'Jack', '5484522']],
 'lastrowid': 3}
```


### DROP a table

In the default authorization setting, a client is not allowed to drop any table.

```python
result = client.execute("DROP TABLE stocks")
pprint(result)
```

```python
{'error': {'message': 'sqlite3.DatabaseError: not authorized',
           'type': 'sqlite3.DatabaseError'},
 'items': []}
```

### 
```python

with client:
  result = client.execute("SELECT * FROM STUDENTS")

```

```python
{'error': {'message': 'sqlite3.OperationalError: no such table: STUDENTS',
           'type': 'sqlite3.OperationalError'},
 'items': []}
```

### SQLiteClient clean up

When you use `zeromq` sockets in a programming language like Python, objects get automatically freed for you. 
However, if you want to explicitly perform clean up and free the I/O resources, there are 2 options. 
You can either call the `cleanup()` method or execute queries in the context of the client i.e. `with` statement.

Call `cleanup()`

```python
client = SQLiteClient(connect_address="tcp://127.0.0.1:5001")
args = ('IBM',)
result = client.execute("SELECT * FROM stocks WHERE symbol = ?", *args)
client.cleanup()
```

Use `with` contextmanager

```python

client = SQLiteClient(connect_address="tcp://127.0.0.1:5001")
args = ('IBM',)
with client:
  result = client.execute("SELECT * FROM stocks WHERE symbol = ?", *args)

```

## Backup

With `sqlite-rx`, database backup can be scheduled to run regularly during Server startup. 
Under the hood, this uses SQLite's Online [Backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup) API. The Backup function runs as a daemon thread and it makes backup even while the database is being accessed by other clients. 

You can specify `backup_interval` (time in seconds) to control how frequently backup should be performed. 

```python

def main():

    # database is a path-like object giving the pathname 
    # of the database file to be opened. 
    
    # You can use ":memory:" to open a database connection to a database 
    # that resides in RAM instead of on disk

    server = SQLiteServer(database="main.db",
                          bind_address="tcp://127.0.0.1:5000",
                          backup_database='backup.db',
                          backup_interval=500)
    server.start()
    server.join()

if __name__ == '__main__':
    main()

```
### Constraints
- Requires Python >= 3.7 
  - Backup is performed using sqlite3 backup API which was introduced in Python 3.7
- Not supported on Windows


## Generic Default Authorization Policy

```python
DEFAULT_AUTH_CONFIG = {
            sqlite3.SQLITE_OK: {
                sqlite3.SQLITE_CREATE_INDEX,
                sqlite3.SQLITE_CREATE_TABLE,
                sqlite3.SQLITE_CREATE_TEMP_INDEX,
                sqlite3.SQLITE_CREATE_TEMP_TABLE,
                sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
                sqlite3.SQLITE_CREATE_TEMP_VIEW,
                sqlite3.SQLITE_CREATE_TRIGGER,
                sqlite3.SQLITE_CREATE_VIEW,
                sqlite3.SQLITE_INSERT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_TRANSACTION,
                sqlite3.SQLITE_UPDATE,
                sqlite3.SQLITE_ATTACH,
                sqlite3.SQLITE_DETACH,
                sqlite3.SQLITE_ALTER_TABLE,
                sqlite3.SQLITE_REINDEX,
                sqlite3.SQLITE_ANALYZE,
                },

            sqlite3.SQLITE_DENY: {
                sqlite3.SQLITE_DELETE,
                sqlite3.SQLITE_DROP_INDEX,
                sqlite3.SQLITE_DROP_TABLE,
                sqlite3.SQLITE_DROP_TEMP_INDEX,
                sqlite3.SQLITE_DROP_TEMP_TABLE,
                sqlite3.SQLITE_DROP_TEMP_TRIGGER,
                sqlite3.SQLITE_DROP_TEMP_VIEW,
                sqlite3.SQLITE_DROP_TRIGGER,
                sqlite3.SQLITE_DROP_VIEW,
            },

            sqlite3.SQLITE_IGNORE: {
                sqlite3.SQLITE_PRAGMA
            }

}
```

You can define your own authorization policy in a python dictionary(as shown above) and pass it to the `SQLiteServer` class
as `auth_config` parameter.
It is recommended you **do not** override the `SQLITE_PRAGMA` action as the database starts in `pragma journal_mode=wal` mode 


# CLI

`sqlite-server` is a console script to start an SQLiteServer.

```text
Usage: sqlite-server [OPTIONS]

Options:
  --log-level [CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|NOTSET]
                                  Logging level  [default: INFO]

  --advertise-host TEXT           Host address on which to run the
                                  SQLiteServer  [default: 0.0.0.0]

  --port TEXT                     Port on which SQLiteServer will listen for
                                  connection requests  [default: 5000]

  --database TEXT                 Path like object giving the database name.
                                  You can use `:memory:` for an in-memory
                                  database  [default: :memory:]

  --zap / --no-zap                True, if you want to enable ZAP
                                  authentication  [default: no-zap]

  --curvezmq / --no-curvezmq      True, if you want to enable CurveZMQ
                                  encryption  [default: no-curvezmq]

  --curve-dir TEXT                Curve Key directory

  --key-id TEXT                   Server key ID

  --backup-database TEXT          Path to the backup database

  --backup-interval FLOAT         Backup interval in seconds  [default: 600.0]

  --help                          Show this message and exit.
```

All docker examples use this console script as an entrypoint

# Secure Client and Server Setup

Please read the [link](https://github.com/aosingh/sqlite_rx/wiki/Secure-Client-Server-Setup) for a detailed explanation on how to setup a secure client/server communication.
This link also explains how to setup CurveZMQ encryption and ZAP authentication

# Docker Examples

The following `docker-compose` examples using the docker image [`aosingh/sqlite_rx`](https://hub.docker.com/r/aosingh/sqlite_rx)


`sqlite-server` CLI is used in all the docker examples

## In-memory SQLite Database

```yaml
version: "3"
services:
  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --log-level DEBUG
    ports:
    - 5000:5000

```

- Note that in the docker container the server listens on port `5000` so, do enable port forwarding on the host machine

## On Disk SQLite Database with Backup

docker volume is used to persist the database file on the host's file system

```yaml

version: "3"
services:

  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --log-level DEBUG --database /data/database.db --backup-database /data/backup.db
    ports:
      - 5000:5000
    volumes:
      - data:/data

volumes:
  data: {}
```

- Named docker volume `data` is mounted to `/data` location in the container
- `sqlite-server` CLI accepts `--database` option which is the database path in the container. 
Form is `/data/<dbname>.db`


## SQLite Database server with CurveZMQ encryption

CurveZMQ is a protocol for secure messaging across the Internet that closely follows the CurveCP security handshake. `curve-keygen` is a script (packaged with sqlite_rx) which is modeled after `ssh-keygen` to generate public and private keys.
Curve Key Generation uses an OpenSSH like directory: `~/.curve`

We need public keys for both servers and clients. We differentiate this by running the `curve-keygen` script in either client or server mode.

Once the keys have been generated, we can enable `CurveZMQ` encryption in the following 
way

```yaml

version: "3"
services:

  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --curvezmq --log-level DEBUG --database /data/database.db --key-id id_server_Abhisheks-MacBook-Pro.local_curve
    ports:
      - 5000:5000
    volumes:
      - data:/data
      - /Users/as/.curve:/root/.curve

volumes:
  data: {}
```

- `sqlite-server` CLI accepts `--curvezmq` boolean flag to enable encryption
- `sqlite-server` CLI accepts `--key-id` which is the server key id available at `/root/.curve` location
- `/Users/as/.curve` (on host machine) is mapped to `/root/.curve` in the docker container. 


## SQLite Database server with CurveZMQ encryption and ZAP authentication

ZeroMQ Authentication protocol

Setting `--zap = True` will restrict connections to clients whose public keys are in the `/root/.curve/authorized_clients/` directory. Set this to `False` to allow any client with the server's
public key to connect, without requiring the server to possess each client's public key.


```yaml

version: "3"
services:

  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --zap --curvezmq --log-level DEBUG --database /data/database.db --key-id id_server_Abhisheks-MacBook-Pro.local_curve
    ports:
    - 5000:5000
    volumes:
    - data:/data
    - /Users/as/.curve:/root/.curve

volumes:
  data: {}
```

