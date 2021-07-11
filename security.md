# Secure Client Server Setup

## Curve Key Generation

CurveZMQ is a protocol for secure messaging across the Internet that closely follows the CurveCP security handshake.

`curve-keygen` is a script (packaged with sqlite_rx) that is modeled after `ssh-keygen` to generate public and private keys.

Implementation idea is borrowed from https://github.com/danielrobbins/ibm-dw-zeromq-2/blob/master/curve-keygen

Curve Key Generation uses an OpenSSH like directory: `~/.curve`

We need public keys for both the server and clients.

### Key ID naming

We follow the naming convention as shown below.

```python
server_key_id = "id_server_{}_curve".format(socket.gethostname())
client_key_id = "id_client_{}_curve".format(socket.gethostname())
```

Run the script with the option `--help`

```bash
curve-keygen --help
usage: curve-keygen [-h] [--mode MODE]

optional arguments:
  -h, --help   show this help message and exit
  --mode MODE  `client` or `server`
```


### Generate Server public and private keys

Run the following command

```bash

 curve-keygen --mode=server

```

You should see the keys generated 

```
cd ~/.curve

ls -lrt

-rw-------  1 abhishek  staff  313 Oct 24 15:13 id_server_Abhisheks-MBP_curve.key_secret
-rw-------  1 abhishek  staff  364 Oct 24 15:13 id_server_Abhisheks-MBP_curve.key
drwx------  2 abhishek  staff   68 Oct 24 15:13 authorized_clients
```

Notice, in `server` mode, the script also creates a directory called `authorized_clients`
This will be used in case you want the server to respond to queries only from known clients. 
You will need to place the client's public keys in this directory. 

### Generate Client's private and public keys

```bash
curve-keygen --mode=client
```

```bash

cd ~/.curve

ls -lrt

-rw-------  1 abhishek  staff  313 Oct 24 15:20 id_client_Abhisheks-MBP_curve.key_secret
-rw-------  1 abhishek  staff  364 Oct 24 15:20 id_client_Abhisheks-MBP_curve.key
```

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

**OUTPUT**

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

```
