"""SQLite connection and table setup."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

DATABASE_FILE = Path(__file__).resolve().parent.parent / "store.db"


@contextmanager
def database_connection() -> Iterator[sqlite3.Connection]:
    """Open a database connection and always close it after the operation.

    Everything done inside one `with` block is a single transaction: it is
    committed if the block succeeds and rolled back if any error is raised.
    """

    connection = sqlite3.connect(DATABASE_FILE)
    connection.row_factory = sqlite3.Row
    # SQLite ignores FOREIGN KEY rules unless this is turned on for every connection.
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    """Create the tables the first time the app runs."""

    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL CHECK (price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
                reorder_level INTEGER NOT NULL DEFAULT 5 CHECK (reorder_level >= 0)
            );

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact TEXT,
                balance REAL NOT NULL DEFAULT 0 CHECK (balance >= 0)
            );

            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER REFERENCES customers (id),
                sale_date TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                payment_type TEXT NOT NULL CHECK (payment_type IN ('cash', 'credit')),
                total REAL NOT NULL DEFAULT 0,
                CHECK (payment_type = 'cash' OR customer_id IS NOT NULL)
            );

            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL REFERENCES sales (id),
                product_id INTEGER NOT NULL REFERENCES products (id),
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL
            );
            """
        )
