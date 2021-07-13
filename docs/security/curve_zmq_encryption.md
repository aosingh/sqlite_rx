---
layout: default
title: CurveZMQ Encryption
parent: Secure Client Server Setup
nav_order: 2
---

## CurveZMQ Encryption

Start the server with the correct server key id. Make sure the private and public keys are locally accessible to the server script in the `~/.curve` directory.

### Server Startup

```python

import socket
from sqlite_rx.server import SQLiteServer

def main():
    server_key_id = "id_server_{}_curve".format(socket.gethostname())
    server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                          use_encryption=True,
                          server_curve_id=server_key_id,
                          database=":memory:")
    server.start()
    server.join()



if __name__ == "__main__":
    main()

````
Start the server and you should see the following logs

```bash

python server.py 

2019-10-24 17:03:25,728 - INFO     server.py:41  Setting up encryption using CurveCP
2019-10-24 17:03:25,728 - INFO     auth.py:233  Secure setup completed using on tcp://127.0.0.1:5001 using curve key id_server_Abhisheks-MBP_curve.
2019-10-24 17:03:25,730 - INFO     server.py:41  Server Event Loop started
```

### Client Startup

Now, let's start the client. 

The client should know the server's public key id and the server's public key should be locally accessible to the client in the `~/.curve` directory.

First, for fun, let's set `use_encryption=False` and see the output

```python

import socket
from pprint import pprint

from sqlite_rx.client import SQLiteClient

client_key_id = "id_client_{}_curve".format(socket.gethostname())
server_key_id = "id_server_{}_curve".format(socket.gethostname())

client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                      server_curve_id=server_key_id,
                      client_curve_id=client_key_id,
                      use_encryption=False)

result = client.execute("CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)")
pprint(result)
```

After the default number of retries, the client abandons the request as the server does not respond. So, if the server starts with `use_encryption = True` then clients should also do the same

```bash

python client.py 
2019-10-24 17:13:45,350 - INFO     client.py:58  Initializing Client
2019-10-24 17:13:45,351 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:13:45,351 - INFO     client.py:71  Executing query CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real) for client python@Abhisheks-MBP_140736436749248
2019-10-24 17:13:45,351 - INFO     client.py:95  Preparing to send request
2019-10-24 17:13:47,856 - WARNING  client.py:119  No response from server, Client will disconnect and retry..
2019-10-24 17:13:47,857 - INFO     client.py:125  Reconnecting and resending request {'client_id': 'python@Abhisheks-MBP_140736436749248', 'query': 'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)', 'params': (), 'execute_many': False, 'execute_script': False}
2019-10-24 17:13:47,857 - INFO     client.py:58  Initializing Client
2019-10-24 17:13:47,857 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:13:50,361 - WARNING  client.py:119  No response from server, Client will disconnect and retry..
2019-10-24 17:13:50,361 - INFO     client.py:125  Reconnecting and resending request {'client_id': 'python@Abhisheks-MBP_140736436749248', 'query': 'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)', 'params': (), 'execute_many': False, 'execute_script': False}
2019-10-24 17:13:50,362 - INFO     client.py:58  Initializing Client
2019-10-24 17:13:50,362 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:13:52,867 - WARNING  client.py:119  No response from server, Client will disconnect and retry..
2019-10-24 17:13:52,868 - INFO     client.py:125  Reconnecting and resending request {'client_id': 'python@Abhisheks-MBP_140736436749248', 'query': 'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)', 'params': (), 'execute_many': False, 'execute_script': False}
2019-10-24 17:13:52,868 - INFO     client.py:58  Initializing Client
2019-10-24 17:13:52,868 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:13:55,370 - WARNING  client.py:119  No response from server, Client will disconnect and retry..
2019-10-24 17:13:55,370 - INFO     client.py:125  Reconnecting and resending request {'client_id': 'python@Abhisheks-MBP_140736436749248', 'query': 'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)', 'params': (), 'execute_many': False, 'execute_script': False}
2019-10-24 17:13:55,371 - INFO     client.py:58  Initializing Client
2019-10-24 17:13:55,371 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:13:57,877 - WARNING  client.py:119  No response from server, Client will disconnect and retry..
2019-10-24 17:13:57,877 - ERROR    client.py:123  Server seems to be offline, abandoning
'Result is None'
```

The correct way to do is `use_encryption = True`
```python

import socket
from pprint import pprint

from sqlite_rx.client import SQLiteClient

client_key_id = "id_client_{}_curve".format(socket.gethostname())
server_key_id = "id_server_{}_curve".format(socket.gethostname())

client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                      server_curve_id=server_key_id,
                      client_curve_id=client_key_id,
                      use_encryption=True)

result = client.execute("CREATE TABLE stocks_2 (date text, trans text, symbol text, qty real, price real)")
pprint("Result is %s" % result)

```

```bash
2019-10-24 17:18:40,492 - INFO     client.py:58  Initializing Client
2019-10-24 17:18:40,493 - INFO     auth.py:289  Client connecting to tcp://127.0.0.1:5001 (key id_server_Abhisheks-MBP_curve) using curve key 'id_client_Abhisheks-MBP_curve'.
2019-10-24 17:18:40,493 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:18:40,493 - INFO     client.py:71  Executing query CREATE TABLE stocks_2 (date text, trans text, symbol text, qty real, price real) for client python@Abhisheks-MBP_140736436749248
2019-10-24 17:18:40,493 - INFO     client.py:95  Preparing to send request
"Result is {'items': [], 'error': None}"

```


