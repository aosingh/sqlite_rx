import logging.config
import os
import shutil
import socket
import tempfile
import unittest
from contextlib import contextmanager

from sqlite_rx import get_default_logger_settings
from sqlite_rx.auth import KeyGenerator
from sqlite_rx.client import SQLiteClient
from sqlite_rx.server import SQLiteServer

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))

@contextmanager
def get_server_auth_files():
    with tempfile.TemporaryDirectory() as curve_dir:
        server_key_id = "id_server_{}_curve".format(socket.gethostname())
        key_generator = KeyGenerator(
            destination_dir=curve_dir,
            key_id=server_key_id)
        key_generator.generate()
        server_public_key = os.path.join(
            curve_dir, "{}.key".format(server_key_id))
        server_private_key = os.path.join(
            curve_dir, "{}.key_secret".format(server_key_id))
        yield curve_dir, server_key_id, server_public_key, server_private_key


class TestAuthenticatedConnection(unittest.TestCase):

    def test_table_not_present(self):

        with get_server_auth_files() as auth_files:
            curve_dir, server_key_id, server_public_key, server_private_key = auth_files
            client_key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=curve_dir, key_id=client_key_id)
            key_generator.generate()
            client_public_key = os.path.join(
                curve_dir, "{}.key".format(client_key_id))
            client_private_key = os.path.join(
                curve_dir, "{}.key_secret".format(client_key_id))
            shutil.copyfile(
                client_public_key,
                os.path.join(
                    curve_dir,
                    'authorized_clients',
                    "{}.key".format(client_key_id)))
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  use_zap_auth=True,
                                  use_encryption=True,
                                  curve_dir=curve_dir,
                                  server_curve_id=server_key_id,
                                  database=":memory:")
            server.daemon = True
            server.start()
            client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                                  server_curve_id=server_key_id,
                                  client_curve_id=client_key_id,
                                  curve_dir=curve_dir,
                                  use_encryption=True)

            result = client.execute('SELECT * FROM IDOLS')
            expected_result = {
                'items': [],
                'error': {
                    'message': 'sqlite3.OperationalError: no such table: IDOLS',
                    'type': 'sqlite3.OperationalError'}}
            self.assertIsInstance(result, dict)
            self.assertDictEqual(result, expected_result)

        server.terminate()
        client.shutdown()

    def test_not_present_without_zap(self):

        with get_server_auth_files() as auth_files:
            curve_dir, server_key_id, server_public_key, server_private_key = auth_files
            client_key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=curve_dir, key_id=client_key_id)
            key_generator.generate()
            client_public_key = os.path.join(
                curve_dir, "{}.key".format(client_key_id))
            client_private_key = os.path.join(
                curve_dir, "{}.key_secret".format(client_key_id))
            shutil.copyfile(
                client_public_key,
                os.path.join(
                    curve_dir,
                    'authorized_clients',
                    "{}.key".format(client_key_id)))
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  use_zap_auth=False,
                                  use_encryption=True,
                                  curve_dir=curve_dir,
                                  server_curve_id=server_key_id,
                                  database=":memory:")
            server.daemon = True
            server.start()
            client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                                  server_curve_id=server_key_id,
                                  client_curve_id=client_key_id,
                                  curve_dir=curve_dir,
                                  use_encryption=True)

            result = client.execute('SELECT * FROM IDOLS')
            expected_result = {
                'items': [],
                'error': {
                    'message': 'sqlite3.OperationalError: no such table: IDOLS',
                    'type': 'sqlite3.OperationalError'}}
            self.assertIsInstance(result, dict)
            self.assertDictEqual(result, expected_result)

        server.terminate()
        client.shutdown()

    def test_table_creation(self):

        with get_server_auth_files() as auth_files:
            curve_dir, server_key_id, server_public_key, server_private_key = auth_files
            client_key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=curve_dir, key_id=client_key_id)
            key_generator.generate()
            client_public_key = os.path.join(
                curve_dir, "{}.key".format(client_key_id))
            client_private_key = os.path.join(
                curve_dir, "{}.key_secret".format(client_key_id))
            shutil.copyfile(
                client_public_key,
                os.path.join(
                    curve_dir,
                    'authorized_clients',
                    "{}.key".format(client_key_id)))
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  use_zap_auth=True,
                                  use_encryption=True,
                                  curve_dir=curve_dir,
                                  server_curve_id=server_key_id,
                                  database=":memory:")
            server.daemon = True
            server.start()
            client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                                  server_curve_id=server_key_id,
                                  client_curve_id=client_key_id,
                                  curve_dir=curve_dir,
                                  use_encryption=True)

            result = client.execute(
                'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
            expected_result = {"error": None, 'items': []}
            self.assertDictEqual(result, expected_result)

        server.terminate()
        client.shutdown()

    def test_table_creation_without_zap(self):

        with get_server_auth_files() as auth_files:
            curve_dir, server_key_id, server_public_key, server_private_key = auth_files
            client_key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=curve_dir, key_id=client_key_id)
            key_generator.generate()
            client_public_key = os.path.join(
                curve_dir, "{}.key".format(client_key_id))
            client_private_key = os.path.join(
                curve_dir, "{}.key_secret".format(client_key_id))
            shutil.copyfile(
                client_public_key,
                os.path.join(
                    curve_dir,
                    'authorized_clients',
                    "{}.key".format(client_key_id)))
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  use_zap_auth=False,
                                  use_encryption=True,
                                  curve_dir=curve_dir,
                                  server_curve_id=server_key_id,
                                  database=":memory:")
            server.daemon = True
            server.start()
            client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                                  server_curve_id=server_key_id,
                                  client_curve_id=client_key_id,
                                  curve_dir=curve_dir,
                                  use_encryption=True)

            result = client.execute(
                'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
            expected_result = {"error": None, 'items': []}
            self.assertDictEqual(result, expected_result)

        server.terminate()
        client.shutdown()

    def test_table_rows_insertion(self):
        with get_server_auth_files() as auth_files:
            curve_dir, server_key_id, server_public_key, server_private_key = auth_files
            client_key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=curve_dir, key_id=client_key_id)
            key_generator.generate()
            client_public_key = os.path.join(
                curve_dir, "{}.key".format(client_key_id))
            client_private_key = os.path.join(
                curve_dir, "{}.key_secret".format(client_key_id))
            shutil.copyfile(
                client_public_key,
                os.path.join(
                    curve_dir,
                    'authorized_clients',
                    "{}.key".format(client_key_id)))
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  use_zap_auth=True,
                                  use_encryption=True,
                                  curve_dir=curve_dir,
                                  server_curve_id=server_key_id,
                                  database=":memory:")
            server.daemon = True
            server.start()
            client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                                  server_curve_id=server_key_id,
                                  client_curve_id=client_key_id,
                                  curve_dir=curve_dir,
                                  use_encryption=True)
            result = client.execute(
                'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
            expected_result = {"error": None, 'items': []}
            self.assertDictEqual(result, expected_result)
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

            result = client.execute(
                'INSERT INTO stocks VALUES (?,?,?,?,?)',
                *purchases,
                execute_many=True)
            expected_result = {'error': None, 'items': [], 'row_count': 27}
            self.assertDictEqual(result, expected_result)

        server.terminate()
        client.shutdown()

    def test_table_rows_insertion_without_zap(self):
        with get_server_auth_files() as auth_files:
            curve_dir, server_key_id, server_public_key, server_private_key = auth_files
            client_key_id = "id_client_{}_curve".format(socket.gethostname())
            key_generator = KeyGenerator(
                destination_dir=curve_dir, key_id=client_key_id)
            key_generator.generate()
            client_public_key = os.path.join(
                curve_dir, "{}.key".format(client_key_id))
            client_private_key = os.path.join(
                curve_dir, "{}.key_secret".format(client_key_id))
            shutil.copyfile(
                client_public_key,
                os.path.join(
                    curve_dir,
                    'authorized_clients',
                    "{}.key".format(client_key_id)))
            server = SQLiteServer(bind_address="tcp://127.0.0.1:5001",
                                  use_zap_auth=False,
                                  use_encryption=True,
                                  curve_dir=curve_dir,
                                  server_curve_id=server_key_id,
                                  database=":memory:")
            server.daemon = True
            server.start()
            client = SQLiteClient(connect_address="tcp://127.0.0.1:5001",
                                  server_curve_id=server_key_id,
                                  client_curve_id=client_key_id,
                                  curve_dir=curve_dir,
                                  use_encryption=True)
            result = client.execute(
                'CREATE TABLE stocks (date text, trans text, symbol text, qty real, price real)')
            expected_result = {"error": None, 'items': []}
            self.assertDictEqual(result, expected_result)
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

            result = client.execute(
                'INSERT INTO stocks VALUES (?,?,?,?,?)',
                *purchases,
                execute_many=True)
            expected_result = {'error': None, 'items': [], 'row_count': 27}
            self.assertDictEqual(result, expected_result)

        server.terminate()
        client.shutdown()


if __name__ == "__main__":
    unittest.main()
