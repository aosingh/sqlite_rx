---
layout: default
title: CurveZMQ Encryption
parent: Secure Client Server Setup
nav_order: 2
---

## CurveZMQ Encryption
CurveZMQ uses the Curve25519 elliptic curve, which was designed by Daniel J. Bernstein to achieve good performance with short key sizes (256 bits). The protocol establishes short-term session keys for every connection to achieve perfect forward security. Session keys are held in memory and destroyed when the connection is closed. CurveZMQ also addresses replay attacks, amplification attacks, MIM attacks, key thefts, client identification, and various denial-of-service attacks. These are inherited from CurveCP, and are explained later.

To enable CurveZMQ encryption, start the server with the correct certificate name as it appears in `~/.curve` directory. 

## Server

```python

# server.py

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

```text
python server.py 

2021-07-13 23:27:04,798 - INFO - [sqlite_rx.server:run:190] Setting up signal handlers
2021-07-13 23:27:04,799 - INFO - [sqlite_rx.server:setup:47] Python Platform CPython
2021-07-13 23:27:04,800 - INFO - [sqlite_rx.server:setup:48] libzmq version 4.3.4
2021-07-13 23:27:04,800 - INFO - [sqlite_rx.server:setup:49] pyzmq version 22.1.0
2021-07-13 23:27:04,800 - INFO - [sqlite_rx.server:setup:50] tornado version 6.1
2021-07-13 23:27:04,802 - INFO - [sqlite_rx.server:stream:89] Setting up encryption using CurveCP
2021-07-13 23:27:04,803 - INFO - [sqlite_rx.auth:setup_secure_server:232] Secure setup completed using on tcp://127.0.0.1:5000 using curve key id_server_Abhisheks-MacBook-Pro.local_curve
2021-07-13 23:27:04,805 - INFO - [sqlite_rx.server:run:197] SQLiteServer version 1.0.2
2021-07-13 23:27:04,806 - INFO - [sqlite_rx.server:run:198] SQLiteServer (Tornado) i/o loop started..
2021-07-13 23:27:04,806 - INFO - [sqlite_rx.server:run:203] Ready to accept client connections on tcp://127.0.0.1:5000

```

## Client

Server's public certificate should be locally accessible to the client in the `~/.curve` directory. Following snippet shows how you can run the client


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
    result = client.execute("CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)")

```

```text

python client.py

{'error': None, 'items': []}


```





