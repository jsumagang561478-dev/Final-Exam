"""Data models used to validate API input.

These classes only describe data. The SQL lives in app/repositories.py
and app/services.py.
"""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ProductInput(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    stock: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=5, ge=0)


class CustomerInput(BaseModel):
    name: str = Field(min_length=1)
    contact: str | None = None


class PaymentInput(BaseModel):
    """A customer paying off part or all of their utang."""

    amount: float = Field(gt=0)


class SaleItemInput(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class SaleInput(BaseModel):
    customer_id: int | None = None
    payment_type: Literal["cash", "credit"] = "cash"
    items: list[SaleItemInput] = Field(min_length=1)

    @model_validator(mode="after")
    def credit_needs_customer(self):
        if self.payment_type == "credit" and self.customer_id is None:
            raise ValueError("A credit sale needs a customer_id")
        return self
