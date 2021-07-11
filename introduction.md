[![PyPI version](https://badge.fury.io/py/sqlite-rx.svg)](https://pypi.python.org/pypi/sqlite-rx) [![sqlite-rx](https://github.com/aosingh/sqlite_rx/actions/workflows/sqlite_build.yaml/badge.svg)](https://github.com/aosingh/sqlite_rx/actions) [![Downloads](https://pepy.tech/badge/sqlite-rx)](https://pepy.tech/project/sqlite-rx)


[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)]((https://www.python.org/downloads/release/python-370/)) [![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/) [![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Python 3.9](https://img.shields.io/badge/python-3.9-blue.svg)]((https://www.python.org/downloads/release/python-390/))
[![PyPy3.6](https://img.shields.io/badge/python-PyPy3.6-blue.svg)](https://www.pypy.org/index.html)

## Introduction

[SQLite](https://www.sqlite.org/index.html) is a lightweight database written in C. 
The Python programming language has in-built support to interact with the database (locally) which is either stored on disk or in memory.

With `sqlite_rx`, clients should be able to communicate with an `SQLiteServer` in a fast, simple and secure manner and execute queries remotely.

Key Features

- Python Client and Server for [SQLite](https://www.sqlite.org/index.html) database built using [ZeroMQ](http://zguide.zeromq.org/page:all) as the transport layer and [msgpack](https://msgpack.org/index.html) for serialization/deserialization.
- Authentication using [ZeroMQ Authentication Protocol (ZAP)](https://rfc.zeromq.org/spec:27/ZAP/)
- Encryption using [CurveZMQ](http://curvezmq.org/)
- Generic authorization policy during server startup
- Schedule regular backups for on-disk database (Currently not supported on Windows and for Python versions < 3.7)
