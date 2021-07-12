---
layout: default
title: SQLite Client
nav_order: 4
---

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
```

```python
{'error': {'message': 'sqlite3.DatabaseError: not authorized',
           'type': 'sqlite3.DatabaseError'},
 'items': []}
```


### Errors

Error details, if any, is returned in the `error` key as shown below. 

In the example below, the table `STUDENTS` is not found.

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
