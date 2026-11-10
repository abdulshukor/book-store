"""API request and response models for bookstore inventory."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class BookFields(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    author: str = Field(..., min_length=1, max_length=120)
    genre: str = Field(..., min_length=1, max_length=60)
    isbn: str | None = Field(default=None, max_length=32)
    price: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2)
    quantity: int = Field(..., ge=0, le=1_000_000)
    description: str = Field(default="", max_length=1200)

    @field_validator("title", "author", "genre", mode="before")
    @classmethod
    def trim_required_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("isbn", mode="before")
    @classmethod
    def clean_isbn(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("description", mode="before")
    @classmethod
    def clean_description(cls, value: object) -> object:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        return value


class BookCreate(BookFields):
    """Request body for adding a new book."""


class BookUpdate(BookFields):
    """Request body for replacing a book's editable fields."""


class Book(BookFields):
    id: str
    created_at: datetime
    updated_at: datetime


class InventoryStats(BaseModel):
    total_titles: int
    total_copies: int
    inventory_value: Decimal
    low_stock_titles: int
