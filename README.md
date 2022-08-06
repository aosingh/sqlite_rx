# sqlite_rx 
[![PyPI version](https://badge.fury.io/py/sqlite-rx.svg)](https://pypi.python.org/pypi/sqlite-rx) [![sqlite-rx](https://github.com/aosingh/sqlite_rx/actions/workflows/sqlite_build.yaml/badge.svg)](https://github.com/aosingh/sqlite_rx/actions) [![Downloads](https://pepy.tech/badge/sqlite-rx)](https://pepy.tech/project/sqlite-rx)


[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) 
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)]((https://www.python.org/downloads/release/python-390/))
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3100/)
[![PyPy3.7](https://img.shields.io/badge/python-PyPy3.7-blue.svg)](https://www.pypy.org/download.html)
[![PyPy3.8](https://img.shields.io/badge/python-PyPy3.8-blue.svg)](https://www.pypy.org/download.html)
[![PyPy3.9](https://img.shields.io/badge/python-PyPy3.9-blue.svg)](https://www.pypy.org/download.html)


#### Official Documentation -> [https://aosingh.github.io/sqlite_rx/](https://aosingh.github.io/sqlite_rx/)

# Introduction

[SQLite](https://www.sqlite.org/index.html) is a lightweight database written in C. 
Python has in-built support to interact with the database (locally) which is either stored on disk or in memory.

With `sqlite_rx`, clients should be able to communicate with an `SQLiteServer` in a fast, simple and secure manner and execute queries remotely.

Key Features

- Client and Server for [SQLite](https://www.sqlite.org/index.html) database built using [ZeroMQ](http://zguide.zeromq.org/page:all) as the transport layer and [msgpack](https://msgpack.org/index.html) for serialization/deserialization.
- Authentication using [ZeroMQ Authentication Protocol (ZAP)](https://rfc.zeromq.org/spec:27/ZAP/)
- Encryption using [CurveZMQ](http://curvezmq.org/)
- Generic authorization policy during server startup
- Schedule regular backups for on-disk databases


# Install

```commandline
pip install -U sqlite_rx
```

## Supported OS 
- Linux
- MacOS
- Windows

## Supported Python Platforms
- CPython 3.6, 3.7, 3.8, 3.9
- PyPy3.6


# Server

`SQLiteServer` runs in a single thread and follows an event-driven concurrency model (using `tornado's` event loop) which minimizes the cost of concurrent client connections. Following snippet shows how you can start the server process.

```python
# server.py

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


# Client

The following snippet shows how you can instantiate an `SQLiteClient` and execute a simple `CREATE TABLE` query.

```python
# client.py

from sqlite_rx.client import SQLiteClient

client = SQLiteClient(connect_address="tcp://127.0.0.1:5000")

with client:
  query = "CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)"
  result = client.execute(query)

```

```text
>> python client.py

{'error': None, 'items': []}
```

