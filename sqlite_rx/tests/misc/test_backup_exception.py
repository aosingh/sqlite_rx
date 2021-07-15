import sys
import pytest

from sqlite_rx.exception import SQLiteRxBackUpError
from sqlite_rx.server import SQLiteServer


def test_backup_exception():

    if not (sys.version_info.major == 3 and sys.version_info.minor >= 7):
        with pytest.raises(SQLiteRxBackUpError):
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5002", database=":memory:", backup_database='backup.db')