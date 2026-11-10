"""FastAPI routes for bookstore inventory management."""

import logging
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware

from . import storage
from .config import (
    API_HOST,
    API_PORT,
    APP_NAME,
    CORS_ALLOW_CREDENTIALS,
    CORS_ALLOW_HEADERS,
    CORS_ALLOW_METHODS,
    CORS_ALLOW_ORIGINS,
)
from .models import Book, BookCreate, BookUpdate, InventoryStats

logger = logging.getLogger(__name__)

app = FastAPI(
    title=APP_NAME, description="Manage the books in your bookstore", version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Leaf & Lore Bookstore API", "docs": "/docs"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/books", response_model=list[Book])
def list_books(
    q: Annotated[str | None, Query(max_length=160)] = None,
    genre: Annotated[str | None, Query(max_length=60)] = None,
) -> list[Book]:
    return storage.get_all_books(search=q, genre=genre)


@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: str) -> Book:
    book = storage.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate) -> Book:
    created = storage.create_book(book)
    logger.info("Created book %s", created.id)
    return created


@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: str, book: BookUpdate) -> Book:
    updated = storage.update_book(book_id, book)
    if updated is None:
        raise HTTPException(status_code=404, detail="Book not found")
    logger.info("Updated book %s", book_id)
    return updated


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: str) -> Response:
    if not storage.delete_book(book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    logger.info("Deleted book %s", book_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/stats", response_model=InventoryStats)
def stats() -> InventoryStats:
    return storage.get_statistics()


def main() -> None:
    uvicorn.run("backend.main:app", host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    main()
