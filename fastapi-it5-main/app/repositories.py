"""Classes that hold the SQL for products and customers.

Each repository is responsible for one table. Routes call these classes
and never write SQL themselves.
"""

import sqlite3

from app.database import database_connection
from app.errors import ConflictError, NotFoundError


class Repository:
    """Base class: stores the connection factory and shared helpers."""

    table = ""
    label = "Record"

    def __init__(self, connect=database_connection):
        self._connect = connect

    def get(self, record_id: int) -> dict:
        with self._connect() as connection:
            return self._get_or_raise(connection, record_id)

    def delete(self, record_id: int) -> None:
        with self._connect() as connection:
            self._get_or_raise(connection, record_id)
            try:
                connection.execute(
                    f"DELETE FROM {self.table} WHERE id = ?", (record_id,)
                )
            except sqlite3.IntegrityError:
                raise ConflictError(
                    f"{self.label} {record_id} is used by existing sales and cannot be deleted"
                )

    def _get_or_raise(self, connection, record_id: int) -> dict:
        row = connection.execute(
            f"SELECT * FROM {self.table} WHERE id = ?", (record_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"{self.label} {record_id} not found")
        return dict(row)


class ProductRepository(Repository):
    table = "products"
    label = "Product"

    def list_all(self, search: str | None = None) -> list[dict]:
        query = "SELECT * FROM products"
        params: tuple = ()
        if search:
            query += " WHERE name LIKE ?"
            params = (f"%{search}%",)
        with self._connect() as connection:
            rows = connection.execute(query + " ORDER BY name", params).fetchall()
        return [dict(row) for row in rows]

    def low_stock(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM products WHERE stock <= reorder_level ORDER BY stock, name"
            ).fetchall()
        return [dict(row) for row in rows]

    def create(self, product_input) -> dict:
        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO products (name, price, stock, reorder_level) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        product_input.name,
                        product_input.price,
                        product_input.stock,
                        product_input.reorder_level,
                    ),
                )
            except sqlite3.IntegrityError:
                raise ConflictError(f"A product named '{product_input.name}' already exists")
            return self._get_or_raise(connection, cursor.lastrowid)

    def update(self, product_id: int, product_input) -> dict:
        with self._connect() as connection:
            self._get_or_raise(connection, product_id)
            try:
                connection.execute(
                    "UPDATE products SET name = ?, price = ?, stock = ?, reorder_level = ? "
                    "WHERE id = ?",
                    (
                        product_input.name,
                        product_input.price,
                        product_input.stock,
                        product_input.reorder_level,
                        product_id,
                    ),
                )
            except sqlite3.IntegrityError:
                raise ConflictError(f"A product named '{product_input.name}' already exists")
            return self._get_or_raise(connection, product_id)


class CustomerRepository(Repository):
    table = "customers"
    label = "Customer"

    def list_all(self, search: str | None = None) -> list[dict]:
        query = "SELECT * FROM customers"
        params: tuple = ()
        if search:
            query += " WHERE name LIKE ?"
            params = (f"%{search}%",)
        with self._connect() as connection:
            rows = connection.execute(query + " ORDER BY name", params).fetchall()
        return [dict(row) for row in rows]

    def with_balance(self) -> list[dict]:
        """Customers who still owe money."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM customers WHERE balance > 0 ORDER BY balance DESC"
            ).fetchall()
        return [dict(row) for row in rows]

    def create(self, customer_input) -> dict:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO customers (name, contact) VALUES (?, ?)",
                (customer_input.name, customer_input.contact),
            )
            return self._get_or_raise(connection, cursor.lastrowid)

    def update(self, customer_id: int, customer_input) -> dict:
        with self._connect() as connection:
            self._get_or_raise(connection, customer_id)
            connection.execute(
                "UPDATE customers SET name = ?, contact = ? WHERE id = ?",
                (customer_input.name, customer_input.contact, customer_id),
            )
            return self._get_or_raise(connection, customer_id)

    def record_payment(self, customer_id: int, payment_input) -> dict:
        """Reduce a customer's utang by the amount paid."""
        with self._connect() as connection:
            customer = self._get_or_raise(connection, customer_id)
            if payment_input.amount > customer["balance"] + 1e-9:
                raise ConflictError(
                    f"Payment of {payment_input.amount:.2f} is more than the "
                    f"balance of {customer['balance']:.2f}"
                )
            connection.execute(
                "UPDATE customers SET balance = MAX(balance - ?, 0) WHERE id = ?",
                (payment_input.amount, customer_id),
            )
            return self._get_or_raise(connection, customer_id)
