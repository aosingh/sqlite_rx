---
layout: default
title: Authorization Config
nav_order: 6
---

Following python dictionary shows the default authorization policy which is applied during server startup.

```python
DEFAULT_AUTH_CONFIG = {
            sqlite3.SQLITE_OK: {
                sqlite3.SQLITE_CREATE_INDEX,
                sqlite3.SQLITE_CREATE_TABLE,
                sqlite3.SQLITE_CREATE_TEMP_INDEX,
                sqlite3.SQLITE_CREATE_TEMP_TABLE,
                sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
                sqlite3.SQLITE_CREATE_TEMP_VIEW,
                sqlite3.SQLITE_CREATE_TRIGGER,
                sqlite3.SQLITE_CREATE_VIEW,
                sqlite3.SQLITE_INSERT,
                sqlite3.SQLITE_READ,
                sqlite3.SQLITE_SELECT,
                sqlite3.SQLITE_TRANSACTION,
                sqlite3.SQLITE_UPDATE,
                sqlite3.SQLITE_ATTACH,
                sqlite3.SQLITE_DETACH,
                sqlite3.SQLITE_ALTER_TABLE,
                sqlite3.SQLITE_REINDEX,
                sqlite3.SQLITE_ANALYZE,
                },

            sqlite3.SQLITE_DENY: {
                sqlite3.SQLITE_DELETE,
                sqlite3.SQLITE_DROP_INDEX,
                sqlite3.SQLITE_DROP_TABLE,
                sqlite3.SQLITE_DROP_TEMP_INDEX,
                sqlite3.SQLITE_DROP_TEMP_TABLE,
                sqlite3.SQLITE_DROP_TEMP_TRIGGER,
                sqlite3.SQLITE_DROP_TEMP_VIEW,
                sqlite3.SQLITE_DROP_TRIGGER,
                sqlite3.SQLITE_DROP_VIEW,
            },

            sqlite3.SQLITE_IGNORE: {
                sqlite3.SQLITE_PRAGMA
            }

}
```

You can define your own authorization policy in a python dictionary(as shown above) and pass it to the `SQLiteServer` class
as `auth_config` parameter. It is recommended you **do not** override the `SQLITE_PRAGMA` action as the database starts in `pragma journal_mode=wal` mode 