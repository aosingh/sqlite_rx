---
layout: default
title: SQLite Server
nav_order: 3
---

## Server

`SQLiteServer` runs in a single thread and follows an event-driven concurrency model (using `tornado's` event loop) which minimizes the cost of concurrent client connections. Following snippet shows how you can start the server process.

```python
from sqlite_rx.server import SQLiteServer

def main():

    # database is a path-like object giving the pathname 
    # of the database file to be opened. 
    
    # You can use ":memory:" to open a database connection to a database 
    # that resides in RAM instead of on disk

    server = SQLiteServer(database=":memory:",
                          bind_address="tcp://127.0.0.1:5000")
    server.start()
    server.join()

if __name__ == '__main__':
    main()

```