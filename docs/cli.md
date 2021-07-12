---
layout: default
title: Command Line Interface (CLI)
nav_order: 7
---

`sqlite-server` is a console script to start an SQLiteServer.

```text
Usage: sqlite-server [OPTIONS]

Options:
  --log-level [CRITICAL|FATAL|ERROR|WARN|WARNING|INFO|DEBUG|NOTSET]
                                  Logging level  [default: INFO]

  --advertise-host TEXT           Host address on which to run the
                                  SQLiteServer  [default: 0.0.0.0]

  --port TEXT                     Port on which SQLiteServer will listen for
                                  connection requests  [default: 5000]

  --database TEXT                 Path like object giving the database name.
                                  You can use `:memory:` for an in-memory
                                  database  [default: :memory:]

  --zap / --no-zap                True, if you want to enable ZAP
                                  authentication  [default: no-zap]

  --curvezmq / --no-curvezmq      True, if you want to enable CurveZMQ
                                  encryption  [default: no-curvezmq]

  --curve-dir TEXT                Curve Key directory

  --key-id TEXT                   Server key ID

  --backup-database TEXT          Path to the backup database

  --backup-interval FLOAT         Backup interval in seconds  [default: 600.0]

  --help                          Show this message and exit.
```

All docker examples use this console script as an entrypoint