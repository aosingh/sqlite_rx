---
layout: default
title: CurveZMQ Key Generation
nav_order: 1
---
## Curve Key Generation

CurveZMQ is a protocol for secure messaging across the Internet that closely follows the CurveCP security handshake.`curve-keygen` is a script (packaged with sqlite_rx) that is modeled after `ssh-keygen` to generate public and private keys.

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