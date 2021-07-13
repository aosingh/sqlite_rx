---
layout: default
title: Introduction
nav_order: 1
---

[![sqlite-rx](https://github.com/aosingh/sqlite_rx/actions/workflows/sqlite_build.yaml/badge.svg)](https://github.com/aosingh/sqlite_rx/actions) [![Downloads](https://pepy.tech/badge/sqlite-rx)](https://pepy.tech/project/sqlite-rx)


## Introduction

[SQLite](https://www.sqlite.org/index.html) is a lightweight database written in C. 
The Python programming language has in-built support to interact with the database (locally) which is either stored on disk or in memory.

With `sqlite_rx`, clients should be able to communicate with an `SQLiteServer` in a fast, simple and secure manner and execute queries remotely.

Key Features

- Python Client and Server for [SQLite](https://www.sqlite.org/index.html) database built using [ZeroMQ](http://zguide.zeromq.org/page:all) as the transport layer and [msgpack](https://msgpack.org/index.html) for serialization/deserialization.
- Authentication using [ZeroMQ Authentication Protocol (ZAP)](https://rfc.zeromq.org/spec:27/ZAP/)
- Encryption using [CurveZMQ](http://curvezmq.org/)
- Generic authorization policy during server startup
- Schedule regular backups for on-disk databases (Currently not supported on Windows and for Python versions < 3.7)
