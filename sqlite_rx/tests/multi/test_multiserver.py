import os
import platform
import signal
import tempfile
import pytest
import sqlite3
import logging.config
import time

from sqlite_rx import get_default_logger_settings
from sqlite_rx.client import SQLiteClient
from sqlite_rx.multiserver import SQLiteMultiServer

logging.config.dictConfig(get_default_logger_settings(level="DEBUG"))
LOG = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def multi_db_client():
    # Create temporary directory for database files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create paths for multiple databases
        db_files = {
            "db1": os.path.join(temp_dir, "db1.db"),
            "db2": os.path.join(temp_dir, "db2.db"),
            "": os.path.join(temp_dir, "default.db")  # Default database
        }

        # Set up authorization config
        auth_config = {
            sqlite3.SQLITE_OK: {
                sqlite3.SQLITE_DROP_TABLE
            }
        }

        # Create and start the multi-database server
        server = SQLiteMultiServer(
            bind_address="tcp://127.0.0.1:5555",
            default_database=db_files[""],
            database_map={
                "db1": db_files["db1"],
                "db2": db_files["db2"]
            },
            auth_config=auth_config
        )
        server.start()
        LOG.info("Started Test SQLiteMultiServer")
        # Call health check directly instead of through the client
        status = server.get_health_info()
        print(f"Server status: {status}")

        # Create clients for each database
        clients = {
            "default": SQLiteClient(connect_address="tcp://127.0.0.1:5555"),
            "db1": SQLiteClient(connect_address="tcp://127.0.0.1:5555", database_name="db1"),
            "db2": SQLiteClient(connect_address="tcp://127.0.0.1:5555", database_name="db2")
        }

        # Give the server time to start up
        time.sleep(1)

        # Yield clients and database paths for tests
        yield {
            "clients": clients,
            "db_files": db_files
        }

        # Clean up
        if platform.system().lower() == 'windows':
            os.system("taskkill /F /pid " + str(server.pid))
        else:
            os.kill(server.pid, signal.SIGINT)
        server.join()

        for client in clients.values():
            client.cleanup()


def test_database_isolation(multi_db_client):
    """Test that each database is isolated from the others."""
    clients = multi_db_client["clients"]
    
    # Add debugging
    print("Starting test_database_isolation")
    
    # Create a table in the default database
    default_result = clients["default"].execute('CREATE TABLE default_table (id INTEGER PRIMARY KEY, name TEXT)')
    print(f"Default create table result: {default_result}")
    
    # Create a table in db1
    db1_result = clients["db1"].execute('CREATE TABLE db1_table (id INTEGER PRIMARY KEY, value INTEGER)')
    print(f"DB1 create table result: {db1_result}")
    
    # Create a table in db2
    db2_result = clients["db2"].execute('CREATE TABLE db2_table (id INTEGER PRIMARY KEY, data TEXT)')
    print(f"DB2 create table result: {db2_result}")
    
    # Insert data
    insert_default = clients["default"].execute('INSERT INTO default_table (name) VALUES (?)', ('Default Record',))
    print(f"Default insert result: {insert_default}")
    
    insert_db1 = clients["db1"].execute('INSERT INTO db1_table (value) VALUES (?)', (42,))
    print(f"DB1 insert result: {insert_db1}")
    
    insert_db2 = clients["db2"].execute('INSERT INTO db2_table (data) VALUES (?)', ('DB2 Data',))
    print(f"DB2 insert result: {insert_db2}")
    
    # Verify data in each database
    default_result = clients["default"].execute('SELECT * FROM default_table')
    print(f"Default select result: {default_result}")
    assert len(default_result["items"]) == 1, f"Expected 1 item in default_table, got {len(default_result['items'])}"
    
    db1_result = clients["db1"].execute('SELECT * FROM db1_table')
    print(f"DB1 select result: {db1_result}")
    assert len(db1_result["items"]) == 1, f"Expected 1 item in db1_table, got {len(db1_result['items'])}"
    
    db2_result = clients["db2"].execute('SELECT * FROM db2_table')
    print(f"DB2 select result: {db2_result}")
    assert len(db2_result["items"]) == 1, f"Expected 1 item in db2_table, got {len(db2_result['items'])}"
    


def test_multiple_connections(multi_db_client):
    """Test that multiple clients can connect to the same database."""
    clients = multi_db_client["clients"]
    
    # Create another client for db1
    db1_client2 = SQLiteClient(connect_address="tcp://127.0.0.1:5555", database_name="db1")
    
    try:
        # First client creates and inserts data
        clients["db1"].execute('CREATE TABLE shared_table (id INTEGER PRIMARY KEY, value TEXT)')
        clients["db1"].execute('INSERT INTO shared_table (value) VALUES (?)', ('Data from client 1',))
        
        # Second client can read and modify the data
        read_result = db1_client2.execute('SELECT * FROM shared_table')
        assert len(read_result["items"]) == 1
        assert read_result["items"][0][1] == 'Data from client 1'
        
        db1_client2.execute('INSERT INTO shared_table (value) VALUES (?)', ('Data from client 2',))
        
        # First client can see the changes
        updated_result = clients["db1"].execute('SELECT * FROM shared_table ORDER BY id')
        assert len(updated_result["items"]) == 2
        assert updated_result["items"][0][1] == 'Data from client 1'
        assert updated_result["items"][1][1] == 'Data from client 2'
    finally:
        db1_client2.cleanup()


def test_complex_queries(multi_db_client):
    """Test that complex queries work correctly."""
    clients = multi_db_client["clients"]
    
    # Set up schema
    clients["db1"].execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            in_stock INTEGER
        )
    ''')
    
    # Insert multiple records
    products = [
        (1, 'Laptop', 999.99, 10),
        (2, 'Smartphone', 499.99, 20),
        (3, 'Headphones', 99.99, 30),
        (4, 'Tablet', 399.99, 15),
        (5, 'Monitor', 299.99, 5),
    ]
    
    clients["db1"].execute(
        'INSERT INTO products (id, name, price, in_stock) VALUES (?, ?, ?, ?)',
        *products,
        execute_many=True
    )
    
    # Test complex SELECT with filtering
    result = clients["db1"].execute(
        'SELECT * FROM products WHERE price > ? AND in_stock > ? ORDER BY price DESC',
        (300.0, 5)
    )
    
    assert len(result["items"]) == 3
    assert result["items"][0][0] == 1  # Laptop
    assert result["items"][1][0] == 2  # Smartphone
    assert result["items"][2][0] == 4  # Tablet
    
    # Test aggregation
    agg_result = clients["db1"].execute(
        'SELECT COUNT(*), SUM(price), AVG(in_stock) FROM products'
    )
    
    assert agg_result["items"][0][0] == 5  # Count
    assert abs(agg_result["items"][0][1] - sum(item[2] for item in products) < 0.01)  # Sum
    assert abs(agg_result["items"][0][2] - 16.0) < 0.01  # Average
    
    # Test UPDATE
    update_result = clients["db1"].execute(
        'UPDATE products SET in_stock = in_stock - 1 WHERE id = ?',
        (1,)
    )
    
    check_result = clients["db1"].execute('SELECT in_stock FROM products WHERE id = ?', (1,))
    assert check_result["items"][0][0] == 9
