import logging.config
import unittest

from sqlite_rx import get_default_logger_settings
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))


class TestUnAuthenticatedServer(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  database=":memory:")
        cls.server.daemon = True
        cls.server.start()
        cls.client = SQLiteClient(connect_address="tcp://127.0.0.1:5001")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        cls.client.shutdown()

    def test_table_creation(self):
        result = self.client.execute(
            'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
        expected_result = {"error": None, 'items': []}
        self.assertDictEqual(result, expected_result)

    def test_table_rows_insertion(self):
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

        result = self.client.execute(
            'INSERT INTO stocks VALUES (?,?,?,?,?)',
            *purchases,
            execute_many=True)
        expected_result = {'error': None, 'items': [], 'row_count': 27}
        self.assertDictEqual(result, expected_result)

    def test_table_not_present(self):
        result = self.client.execute('SELECT * FROM IDOLS')
        self.assertIsInstance(result, dict)


    def test_sql_script(self):
        script = '''CREATE TABLE users(id INTEGER PRIMARY KEY, name TEXT, phone TEXT);
                    CREATE TABLE accounts(id INTEGER PRIMARY KEY, description TEXT);

                    INSERT INTO users(name, phone) VALUES ('John', '5557241'), 
                     ('Adam', '5547874'), ('Jack', '5484522');'''
        expected_result = {"error": None, 'items': []}
        result = self.client.execute(script, execute_script=True)
        self.assertDictEqual(result, expected_result)


if __name__ == "__main__":
    unittest.main()
