---
layout: default
title: SQLite database backup
nav_order: 5
---

Database backup can be scheduled to run regularly during Server startup. Under the hood, this uses SQLite's online [backup](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup) API. The Backup function runs as a daemon thread and makes backup even while the database is being accessed by other clients. 

You can specify `backup_interval` (time in seconds) to control how frequently backup should be performed. 

```python

def main():

    # database is a path-like object giving the pathname 
    # of the database file to be opened. 
    
    # You can use ":memory:" to open a database connection to a database 
    # that resides in RAM instead of on disk

    server = SQLiteServer(database="main.db",
                          bind_address="tcp://127.0.0.1:5000",
                          backup_database='backup.db',
                          backup_interval=500)
    server.start()
    server.join()

if __name__ == '__main__':
    main()

```
### Constraints
- Requires Python >= 3.7 
  - Backup is performed using sqlite3 backup API which was introduced in Python 3.7
- Not supported on Windows