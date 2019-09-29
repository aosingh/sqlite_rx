# sqlite_rx [![Travis](https://travis-ci.org/aosingh/lexpy.svg?branch=master)](https://travis-ci.org/aosingh/sqlite_rx) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)

- Python Client and Server process for SQLite database built using ZMQ and msgpack.
- Authentication using ZeroMQ Authentication Protcol (ZAP)
- Encryption using CurveMQ
- Define Authorization policies


***Please Note that detailed documentation explaining the configuration options for both Client and Server is in-progress. 
Below you can find the steps to get started***


# Install
```commandline
pip install sqlite_rx
```

# Examples

## Server

```python
from sqlite_rx.server import SQLiteServer


def main():
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
from pprint import pprint # (We will use the pprint later. This is not needed to instantiate an SQLite Client)

from sqlite_rx.client import SQLiteClient
client = SQLiteClient(connect_address="tcp://127.0.0.1:5000")
```

### SELECT statement: (Table not present)
```python

result = client.execute('''SELECT * FROM IDOLS''')
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

result = client.execute('''CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)''')
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

result = client.execute('INSERT INTO stocks VALUES (?,?,?,?,?)', *purchases, execute_many=True)
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

Note: In the default setting a client is not allowed to drop any table.

```python
result = client.execute('DROP TABLE stocks')
pprint(result)
```

OUTPUT

```text
{'error': {'message': 'sqlite3.DatabaseError: not authorized',
           'type': 'sqlite3.DatabaseError'},
 'items': []}
```



