"""Create the FastAPI app and connect its routes."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import initialize_database
from app.errors import ConflictError, NotFoundError
from app.models import CustomerInput, PaymentInput, ProductInput, SaleInput
from app.repositories import CustomerRepository, ProductRepository
from app.services import SaleService

app = FastAPI(title="Sari-Sari Store API")

products = ProductRepository()
customers = CustomerRepository()
sales = SaleService()


@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, error: NotFoundError):
    return JSONResponse(status_code=404, content={"detail": str(error)})


@app.exception_handler(ConflictError)
def handle_conflict(request: Request, error: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.get("/")
def home():
    return {"message": "Welcome! Visit /docs to try the API."}


# ---------- Products ----------
# Fixed paths such as /products/low-stock must come before /products/{product_id}.


@app.get("/products")
def list_products(search: str | None = None):
    return {"products": products.list_all(search=search)}


@app.get("/products/low-stock")
def low_stock_products():
    return {"products": products.low_stock()}


@app.get("/products/{product_id}")
def get_product(product_id: int):
    return {"product": products.get(product_id)}


@app.post("/products", status_code=201)
def create_product(product: ProductInput):
    return {"product": products.create(product)}


@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductInput):
    return {"product": products.update(product_id, product)}


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    products.delete(product_id)
    return {"message": "Product deleted successfully"}


# ---------- Customers ----------


@app.get("/customers")
def list_customers(search: str | None = None):
    return {"customers": customers.list_all(search=search)}


@app.get("/customers/with-balance")
def customers_with_balance():
    return {"customers": customers.with_balance()}


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int):
    return {"customer": customers.get(customer_id)}


@app.post("/customers", status_code=201)
def create_customer(customer: CustomerInput):
    return {"customer": customers.create(customer)}


@app.put("/customers/{customer_id}")
def update_customer(customer_id: int, customer: CustomerInput):
    return {"customer": customers.update(customer_id, customer)}


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: int):
    customers.delete(customer_id)
    return {"message": "Customer deleted successfully"}


@app.post("/customers/{customer_id}/payments")
def pay_utang(customer_id: int, payment: PaymentInput):
    return {"customer": customers.record_payment(customer_id, payment)}


# ---------- Sales ----------


@app.get("/sales")
def list_sales(date: str | None = None):
    return {"sales": sales.list_sales(sale_date=date)}


@app.get("/sales/daily-summary")
def daily_summary(date: str | None = None):
    return {"summary": sales.daily_summary(sale_date=date)}


@app.get("/sales/{sale_id}")
def get_sale(sale_id: int):
    return {"sale": sales.get_sale(sale_id)}


@app.post("/sales", status_code=201)
def create_sale(sale: SaleInput):
    return {"sale": sales.create_sale(sale)}


initialize_database()
