import sys
import platform
import sqlite3
import os
import time

import pytest

from sqlite_rx import backup

sqlite_error_prefix = "sqlite3.OperationalError"

if platform.python_implementation() == "PyPy":
    sqlite_error_prefix = "_sqlite3.OperationalError"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="backup is not supported on windows")
def test_not_present(plain_client):
    if sys.platform.startswith("win"):
        pytest.skip("skipping windows-only tests", allow_module_level=True)
    result = plain_client.client.execute('SELECT * FROM IDOLS')
    expected_result = {
        'items': [],
        'error': {
            'message': '{0}: no such table: IDOLS'.format(sqlite_error_prefix),
            'type': '{0}'.format(sqlite_error_prefix)}}
    assert type(result) == dict
    assert result == expected_result
    

@pytest.mark.skipif(sys.platform.startswith("win"), reason="backup is not supported on windows")
def test_table_creation(plain_client):
    result = plain_client.client.execute('CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
    expected_result = {"error": None, 'items': []}
    assert result == expected_result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="backup is not supported on windows")
def test_table_rows_insertion(plain_client):
    purchases = [('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ('2006-03-28', 'BUY', 'IBM', 1000, 45.00),
                 ('2006-04-05', 'BUY', 'MSFT', 1000, 72.00),
                 ('2006-04-06', 'SELL', 'XOM', 500, 53.00),
                 ]

    result = plain_client.client.execute('INSERT INTO stocks VALUES (?,?,?,?,?)', *purchases, execute_many=True)
    expected_result = {'error': None, 'items': [], 'rowcount': 27}
    assert result == expected_result

    if sys.version_info.major == 3 and sys.version_info.minor >= 7:
        time.sleep(2)  # wait for the backup thread to finish backing up.

        backup_database = plain_client.backup_database
        backup_connection = sqlite3.connect(database=backup_database,
                                            isolation_level=None,
                                            check_same_thread=False)                      
        assert os.path.exists(backup_database) is True
        assert os.path.getsize(backup_database) == os.path.getsize(plain_client.main_database)
        result = backup_connection.execute("SELECT * FROM stocks").fetchall()
        assert len(result) == 27
    