"""
Example of using the SQLiteMultiServer with multiple databases.

This example:
1. Starts a SQLiteMultiServer with multiple databases
2. Connects clients to different databases
3. Shows how to perform operations on each database

Run this in separate terminals:

Terminal 1:
    python -m sqlite_rx.cli.multiserver --tcp-address tcp://127.0.0.1:5555 --database-map '{"users": "users.db", "products": "products.db"}'

Terminal 2:
    python multi_database_example.py
"""

import os
import time
from sqlite_rx.client import SQLiteClient


def main():
    # Create a client connected to the default database
    default_client = SQLiteClient(connect_address="tcp://127.0.0.1:5555")
    
    # Create clients for specific databases
    users_client = SQLiteClient(connect_address="tcp://127.0.0.1:5555", database_name="users")
    products_client = SQLiteClient(connect_address="tcp://127.0.0.1:5555", database_name="products")
    
    # Clean up any existing files for demo purposes
    for db_file in ["users.db", "products.db"]:
        if os.path.exists(db_file):
            os.remove(db_file)
    
    # Set up tables in each database
    try:
        # Create users table in the users database
        users_client.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                created_at TEXT
            )
        """)
        print("Created users table")
        
        # Create products table in the products database
        products_client.execute("""
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                price REAL,
                in_stock INTEGER
            )
        """)
        print("Created products table")
        
        # Insert data into users database
        users = [
            (1, "John Doe", "john@example.com", "2023-01-01"),
            (2, "Jane Smith", "jane@example.com", "2023-01-02"),
            (3, "Bob Johnson", "bob@example.com", "2023-01-03"),
        ]
        users_client.execute(
            "INSERT INTO users (id, name, email, created_at) VALUES (?, ?, ?, ?)",
            *users,
            execute_many=True
        )
        print("Inserted user data")
        
        # Insert data into products database
        products = [
            (1, "Laptop", 999.99, 10),
            (2, "Smartphone", 499.99, 20),
            (3, "Headphones", 99.99, 30),
            (4, "Tablet", 399.99, 15),
        ]
        products_client.execute(
            "INSERT INTO products (id, name, price, in_stock) VALUES (?, ?, ?, ?)",
            *products,
            execute_many=True
        )
        print("Inserted product data")
        
        # Query data from the users database
        result = users_client.execute("SELECT * FROM users")
        print("\nUsers:")
        for user in result["items"]:
            print(f"  {user[0]}. {user[1]} ({user[2]})")
        
        # Query data from the products database
        result = products_client.execute("SELECT * FROM products")
        print("\nProducts:")
        for product in result["items"]:
            print(f"  {product[0]}. {product[1]} - ${product[2]} ({product[3]} in stock)")
        
        # Try to query users table from products client (should fail)
        try:
            result = products_client.execute("SELECT * FROM users")
            print("\nCrossover query result:", result)
        except Exception as e:
            print("\nExpected error when querying users table from products client:", e)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        default_client.cleanup()
        users_client.cleanup()
        products_client.cleanup()


if __name__ == "__main__":
    main()
