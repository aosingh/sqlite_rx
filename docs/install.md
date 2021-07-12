---
layout: default
title: Install
nav_order: 2
---

Python Package Index (PyPI) version:  [1.0.2](https://pypi.org/project/sqlite-rx/)
{: .fs-6 .fw-300 }

You can install `sqlite_rx` via the Python Package Index (PyPI) using `pip`

```commandline
pip install -U sqlite_rx
```

## Supported OS 
- Linux
- MacOS
- Windows

## Supported Python Platforms
- CPython 3.6, 3.7, 3.8, 3.9
- PyPy3.6

## External PyPI Dependencies
Dependencies are defined as install requirements in setup.py. You need not install them separately. 
We use the following external libraries.

- click : To create a Command Line Interface (CLI) for sqlite_rx
- billiard : Multiprocessing library
- msgpack : Used for serialization / deserialization
- pyzmq : Networking library which also acts as a message queue
