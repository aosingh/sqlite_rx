---
layout: default
title: ZAP Authentication
nav_order: 3
---

## ZAP Authentication

ZeroMQ Authentication protocol

The use case for ZAP is a set of servers that need authentication of remote clients

This is controlled by the parameter `use_zap_auth ` 
Setting `use_zap_auth = True` will restrict connections to clients whose public keys are in the `~/.curve/authorized_clients/` directory. Set this to `False` to allow any client with the server's
public key to connect, without requiring the server to possess each client's public key.

Place the client's public key at the server's `~/.curve/authorized_clients/` directory. 

```bash
cd ~/.curve/authorized_clients

ls -lrt

-rw-------  1 abhishek  staff  364 Oct 24 17:28 id_client_Abhisheks-MBP_curve.key
```
Now, let's start the server script

```python
import socket
from sqlite_rx.server import SQLiteServer

def main():
    server_key_id = "id_server_{}_curve".format(socket.gethostname())
    server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                          use_encryption=True,
                          use_zap_auth=True,
                          server_curve_id=server_key_id,
                          database=":memory:")
    try:
       server.start()
    except KeyBoardInterrupt:
       server.stop()


if __name__ == "__main__":
    main()
```

**OUTPUT**

```bash

2019-10-24 17:32:15,550 - INFO     server.py:41  Setting up encryption using CurveCP
2019-10-24 17:32:15,550 - INFO     auth.py:233  Secure setup completed using on tcp://127.0.0.1:5001 using curve key id_server_Abhisheks-MBP_curve.
2019-10-24 17:32:15,551 - INFO     server.py:41  ZAP enabled. 
 Authorizing clients in /Users/abhishek/.curve/authorized_clients.
2019-10-24 17:32:15,553 - INFO     server.py:41  Server Event Loop started

```
Now, let's run the client 

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

**OUTPUT**

```bash
python client.py
2019-10-24 17:34:06,646 - INFO     client.py:58  Initializing Client
2019-10-24 17:34:06,647 - INFO     auth.py:289  Client connecting to tcp://127.0.0.1:5001 (key id_server_Abhisheks-MBP_curve) using curve key 'id_client_Abhisheks-MBP_curve'.
2019-10-24 17:34:06,647 - INFO     client.py:67  client python@Abhisheks-MBP_140736436749248 connected successfully
2019-10-24 17:34:06,647 - INFO     client.py:71  Executing query CREATE TABLE stocks_2 (date text, trans text, symbol text, qty real, price real) for client python@Abhisheks-MBP_140736436749248
2019-10-24 17:34:06,647 - INFO     client.py:95  Preparing to send request
"Result is {'items': [], 'error': None}"