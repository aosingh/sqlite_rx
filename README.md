# sqlite_rx [![Travis](https://travis-ci.org/aosingh/lexpy.svg?branch=master)](https://travis-ci.org/aosingh/sqlite_rx) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)

## Introduction

SQLite is a lightweight database written in C. 
The Python programming language has in-built support to interact with the database(locally) which is either stored on disk or in memory.

With `sqlite_rx`, I have built server and client processes for SQLite. 
This will allow the clients to communicate with the Server in a fast, simple and secure manner and execute queries
remotely

Features

- Python Client and Server for [SQLite](https://www.sqlite.org/index.html) database built using [ZeroMQ](http://zguide.zeromq.org/page:all) and [msgpack](https://msgpack.org/index.html).
- Authentication using [ZeroMQ Authentication Protocol (ZAP)](https://rfc.zeromq.org/spec:27/ZAP/)
- Encryption using [CurveZMQ](http://curvezmq.org/)
- Define generic authorization policies


***Please note that detailed documentation(explaining the configuration options) for both Client and Server is in-progress. 
Below you can find the steps to quickly get started***

# Dependencies
    
    >= python3.x

# Install
```commandline
pip install sqlite_rx
```

# Examples

## Server

```python
from sqlite_rx.server import SQLiteServer


def main():

    # database is a path-like object giving the pathname 
    # of the database file to be opened. 
    
    # You can use ":memory:" to open a database connection to a database 
    # that resides in RAM instead of on disk
    
    server = SQLiteServer(database=":memory:",
                          bind_address="tcp://127.0.0.1:5000")
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()


if __name__ == '__main__':
    main()
```

## Client

A client has a single interface ``execute``

### Instantiate a client

```python
from sqlite_rx.client import SQLiteClient
client = SQLiteClient(connect_address="tcp://127.0.0.1:5000")
```

### SELECT statement: (Table not present)
```python
from pprint import pprint
result = client.execute("SELECT * FROM IDOLS")
pprint(result)

```
OUTPUT
```text
{'error': {'message': 'sqlite3.OperationalError: no such table: IDOLS',
           'type': 'sqlite3.OperationalError'},
 'items': []}
```

### CREATE TABLE statement

```python

result = client.execute("CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)")
pprint(result)
```
OUTPUT
```text
{'error': None, 'items': []}
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
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                ]

result = client.execute("INSERT INTO stocks VALUES (?,?,?,?,?)", *purchases, execute_many=True)
pprint(result)

```
OUTPUT

```text
{'error': None, 'items': [], 'row_count': 27}
```

### SELECT with WHERE clause
```python
args = ('IBM',)
result = client.execute("SELECT * FROM stocks WHERE symbol = ?", *args)
pprint(result)

```
OUTPUT

```text
{'error': None,
 'items': [['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0],
           ['2006-03-28', 'BUY', 'IBM', 1000.0, 45.0]]}
```

### DROP a TABLE

Note: In the default authorization setting, a client is not allowed to drop any table.

```python
result = client.execute("DROP TABLE stocks")
pprint(result)
```

OUTPUT

```text
{'error': {'message': 'sqlite3.DatabaseError: not authorized',
           'type': 'sqlite3.DatabaseError'},
 'items': []}
```

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

You can define your own authorization policy in a python dictionary and pass it to the `SQLiteServer` class
as `auth_config` parameter.
It is recommended you **do not** override the `SQLITE_PRAGMA` action as the database starts in `pragma journal_mode=wal` mode 




