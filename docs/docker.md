---
layout: default
title: Docker Examples
nav_order: 9
---

The following `docker-compose` examples using the docker image [`aosingh/sqlite_rx`](https://hub.docker.com/r/aosingh/sqlite_rx)

`sqlite-server` CLI is used in all the docker examples

## In-memory SQLite Database

```yaml
version: "3"
services:
  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --log-level DEBUG
    ports:
    - 5000:5000

```

- Note that in the docker container the server listens on port `5000` so, do enable port forwarding on the host machine

## On Disk SQLite Database with Backup

docker volume is used to persist the database file on the host's file system

```yaml

version: "3"
services:

  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --log-level DEBUG --database /data/database.db --backup-database /data/backup.db
    ports:
      - 5000:5000
    volumes:
      - data:/data

volumes:
  data: {}
```

- Named docker volume `data` is mounted to `/data` location in the container
- `sqlite-server` CLI accepts `--database` option which is the database path in the container. 
Form is `/data/<dbname>.db`

## SQLite Database server with CurveZMQ encryption

```yaml

version: "3"
services:

  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --curvezmq --log-level DEBUG --database /data/database.db --key-id id_server_Abhisheks-MacBook-Pro.local_curve
    ports:
      - 5000:5000
    volumes:
      - data:/data
      - /Users/as/.curve:/root/.curve

volumes:
  data: {}
```

- `sqlite-server` CLI accepts `--curvezmq` boolean flag to enable encryption
- `sqlite-server` CLI accepts `--key-id` which is the server key id available at `/root/.curve` location
- `/Users/as/.curve` (on host machine) is mapped to `/root/.curve` in the docker container. 

## SQLite Database server with CurveZMQ encryption and ZAP authentication

ZeroMQ Authentication protocol

Setting `--zap = True` will restrict connections to clients whose public keys are in the `/root/.curve/authorized_clients/` directory. Set this to `False` to allow any client with the server's
public key to connect, without requiring the server to possess each client's public key.


```yaml

version: "3"
services:

  sqlite_server:
    image: aosingh/sqlite_rx
    command: sqlite-server --zap --curvezmq --log-level DEBUG --database /data/database.db --key-id id_server_Abhisheks-MacBook-Pro.local_curve
    ports:
    - 5000:5000
    volumes:
    - data:/data
    - /Users/as/.curve:/root/.curve

volumes:
  data: {}
```