---
layout: default
title: Install
nav_order: 2
---

## Release v1.1.1 Installation

You can install `sqlite_rx` via the Python Package Index (PyPI) using `pip`

```commandline
pip install -U sqlite_rx

```

Additionally, to install CLI dependencies use the following command

```commandline
pip install -U 'sqlite-rx[cli]'
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
