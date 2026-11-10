"""CSV persistence, retained from the original sample architecture.

Updates and deletes replace the CSV atomically, so a failure during a write
cannot leave a partially written catalog. A thread lock protects concurrent
requests handled by the same Python process (single-worker local deployment).
"""

import csv
import os
import tempfile
import threading
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from .config import DATA_DIR, LOW_STOCK_THRESHOLD
from .models import Book, BookCreate, BookUpdate, InventoryStats

BOOKS_FILE = Path(DATA_DIR) / "books.csv"
CSV_HEADERS = [
    "id",
    "created_at",
    "updated_at",
    "title",
    "author",
    "genre",
    "isbn",
    "price",
    "quantity",
    "description",
]
_lock = threading.RLock()


def _initialize() -> None:
    BOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not BOOKS_FILE.exists():
        _write_all([])


def _read_all() -> list[Book]:
    if not BOOKS_FILE.exists():
        return []
    with BOOKS_FILE.open("r", newline="", encoding="utf-8") as file:
        return [Book.model_validate(row) for row in csv.DictReader(file)]


def _write_all(books: list[Book]) -> None:
    BOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=BOOKS_FILE.parent,
            prefix=".books-",
            suffix=".tmp",
            delete=False,
        ) as file:
            temp_path = file.name
            writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
            writer.writeheader()
            for book in books:
                record = book.model_dump(mode="json")
                writer.writerow(
                    {header: record.get(header, "") for header in CSV_HEADERS}
                )
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, BOOKS_FILE)
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def get_all_books(search: str | None = None, genre: str | None = None) -> list[Book]:
    with _lock:
        books = _read_all()
    if search:
        needle = search.casefold().strip()
        books = [
            book
            for book in books
            if needle in " ".join([book.title, book.author, book.isbn or ""]).casefold()
        ]
    if genre:
        books = [
            book for book in books if book.genre.casefold() == genre.casefold().strip()
        ]
    return sorted(books, key=lambda book: book.created_at, reverse=True)


def get_book(book_id: str) -> Book | None:
    with _lock:
        return next((book for book in _read_all() if book.id == book_id), None)


def create_book(payload: BookCreate) -> Book:
    with _lock:
        _initialize()
        now = datetime.now(UTC)
        book = Book(
            id=str(uuid4()), created_at=now, updated_at=now, **payload.model_dump()
        )
        books = _read_all()
        books.append(book)
        _write_all(books)
    return book


def update_book(book_id: str, payload: BookUpdate) -> Book | None:
    with _lock:
        books = _read_all()
        for index, old in enumerate(books):
            if old.id == book_id:
                updated = old.model_copy(
                    update={
                        **payload.model_dump(),
                        "updated_at": datetime.now(UTC),
                    }
                )
                books[index] = updated
                _write_all(books)
                return updated
    return None


def delete_book(book_id: str) -> bool:
    with _lock:
        books = _read_all()
        remaining = [book for book in books if book.id != book_id]
        if len(remaining) == len(books):
            return False
        _write_all(remaining)
        return True


def get_statistics() -> InventoryStats:
    with _lock:
        books = _read_all()
    return InventoryStats(
        total_titles=len(books),
        total_copies=sum(book.quantity for book in books),
        inventory_value=sum(
            (book.price * book.quantity for book in books), Decimal("0.00")
        ),
        low_stock_titles=sum(book.quantity <= LOW_STOCK_THRESHOLD for book in books),
    )
