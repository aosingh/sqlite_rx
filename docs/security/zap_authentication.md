---
layout: default
title: ZAP Authentication
parent: Secure Client Server Setup
nav_order: 3
---

## ZAP Authentication

ZeroMQ Authentication protocol.
The use case for ZAP is a set of servers that need authentication of remote clients. Setting `use_zap_auth = True` will restrict connections to clients whose public keys are in the `~/.curve/authorized_clients/` directory. 
Set this to `False` to allow any client with the server's public key to connect, without requiring the server to possess each client's public key.

Place client's public key at the server's `~/.curve/authorized_clients/` directory. 

```bash
cd ~/.curve/authorized_clients

ls -lrt

-rw-------  1 abhishek  staff  364 Oct 24 17:28 id_client_Abhisheks-MBP_curve.key
```
## Server

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
    
    server.start()
    server.join()

if __name__ == "__main__":
    main()
```

```text
>> python server.py

2021-07-14 21:28:54,204 - INFO - [sqlite_rx.server:run:190] Setting up signal handlers
2021-07-14 21:28:54,205 - INFO - [sqlite_rx.server:setup:47] Python Platform CPython
2021-07-14 21:28:54,206 - INFO - [sqlite_rx.server:setup:48] libzmq version 4.3.4
2021-07-14 21:28:54,206 - INFO - [sqlite_rx.server:setup:49] pyzmq version 22.1.0
2021-07-14 21:28:54,207 - INFO - [sqlite_rx.server:setup:50] tornado version 6.1
2021-07-14 21:28:54,209 - INFO - [sqlite_rx.server:stream:89] Setting up encryption using CurveCP
2021-07-14 21:28:54,210 - INFO - [sqlite_rx.auth:setup_secure_server:232] Secure setup completed using on tcp://127.0.0.1:5000 using curve key id_server_Abhisheks-MacBook-Pro.local_curve
2021-07-14 21:28:54,211 - INFO - [sqlite_rx.server:stream:97] ZAP enabled. Authorizing clients in /Users/as/.curve/authorized_clients.
2021-07-14 21:28:54,217 - INFO - [sqlite_rx.server:run:197] SQLiteServer version 1.0.2
2021-07-14 21:28:54,218 - INFO - [sqlite_rx.server:run:198] SQLiteServer (Tornado) i/o loop started..
2021-07-14 21:28:54,218 - INFO - [sqlite_rx.server:run:203] Ready to accept client connections on tcp://127.0.0.1:5000

```
## Client

```python
# client.py

import socket

from sqlite_rx.client import SQLiteClient

client_key_id = "id_client_{}_curve".format(socket.gethostname())
server_key_id = "id_server_{}_curve".format(socket.gethostname())

client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                      server_curve_id=server_key_id,
                      client_curve_id=client_key_id,
                      use_encryption=True)

with client:
    result = client.execute("CREATE TABLE stocks_2 (date text, trans text, symbol text, qty real, price real)")

```

```text
>> python client.py

{'error': None, 'items': []}
```