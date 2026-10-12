"""Business workflows that touch more than one table."""

from datetime import date

from app.database import database_connection
from app.errors import ConflictError, NotFoundError


class SaleService:
    """Records sales and reports on them.

    create_sale is the main transaction of the system. Everything inside its
    single `with` block either happens completely or not at all.
    """

    def __init__(self, connect=database_connection):
        self._connect = connect

    def create_sale(self, sale_input) -> dict:
        with self._connect() as connection:
            if sale_input.customer_id is not None:
                customer = connection.execute(
                    "SELECT id FROM customers WHERE id = ?", (sale_input.customer_id,)
                ).fetchone()
                if customer is None:
                    raise NotFoundError(f"Customer {sale_input.customer_id} not found")

            cursor = connection.execute(
                "INSERT INTO sales (customer_id, payment_type) VALUES (?, ?)",
                (sale_input.customer_id, sale_input.payment_type),
            )
            sale_id = cursor.lastrowid

            total = 0.0
            for item in sale_input.items:
                product = connection.execute(
                    "SELECT id, name, price, stock FROM products WHERE id = ?",
                    (item.product_id,),
                ).fetchone()
                if product is None:
                    raise NotFoundError(f"Product {item.product_id} not found")
                if product["stock"] < item.quantity:
                    raise ConflictError(
                        f"Not enough stock for {product['name']}: "
                        f"{product['stock']} left, {item.quantity} requested"
                    )

                connection.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (item.quantity, item.product_id),
                )
                connection.execute(
                    "INSERT INTO sale_items (sale_id, product_id, quantity, unit_price) "
                    "VALUES (?, ?, ?, ?)",
                    (sale_id, item.product_id, item.quantity, product["price"]),
                )
                total += product["price"] * item.quantity

            total = round(total, 2)
            connection.execute("UPDATE sales SET total = ? WHERE id = ?", (total, sale_id))

            if sale_input.payment_type == "credit":
                connection.execute(
                    "UPDATE customers SET balance = balance + ? WHERE id = ?",
                    (total, sale_input.customer_id),
                )

            return self._fetch_sale(connection, sale_id)

    def get_sale(self, sale_id: int) -> dict:
        with self._connect() as connection:
            return self._fetch_sale(connection, sale_id)

    def list_sales(self, sale_date: str | None = None) -> list[dict]:
        query = "SELECT * FROM sales"
        params: tuple = ()
        if sale_date:
            query += " WHERE date(sale_date) = ?"
            params = (sale_date,)
        with self._connect() as connection:
            rows = connection.execute(query + " ORDER BY id DESC", params).fetchall()
        return [dict(row) for row in rows]

    def daily_summary(self, sale_date: str | None = None) -> dict:
        sale_date = sale_date or date.today().isoformat()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS sales_count,
                    COALESCE(SUM(total), 0) AS total_sales,
                    COALESCE(SUM(CASE WHEN payment_type = 'cash' THEN total END), 0) AS cash_sales,
                    COALESCE(SUM(CASE WHEN payment_type = 'credit' THEN total END), 0) AS credit_sales
                FROM sales
                WHERE date(sale_date) = ?
                """,
                (sale_date,),
            ).fetchone()
        return {"date": sale_date, **dict(row)}

    def _fetch_sale(self, connection, sale_id: int) -> dict:
        sale = connection.execute(
            "SELECT * FROM sales WHERE id = ?", (sale_id,)
        ).fetchone()
        if sale is None:
            raise NotFoundError(f"Sale {sale_id} not found")
        items = connection.execute(
            """
            SELECT sale_items.product_id, products.name AS product_name,
                   sale_items.quantity, sale_items.unit_price,
                   sale_items.quantity * sale_items.unit_price AS subtotal
            FROM sale_items
            JOIN products ON products.id = sale_items.product_id
            WHERE sale_items.sale_id = ?
            ORDER BY sale_items.id
            """,
            (sale_id,),
        ).fetchall()
        return {**dict(sale), "items": [dict(item) for item in items]}
