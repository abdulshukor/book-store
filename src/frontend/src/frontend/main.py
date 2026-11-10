"""Flask/Jinja bookstore frontend, adapted from the supplied study tracker."""

import hmac
import logging
import os
import secrets
from decimal import Decimal
from uuid import UUID

import requests
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(
    32
)  # Set a stable key in production.
app.config.update(
    API_URL=os.getenv("API_URL", "http://127.0.0.1:21002").rstrip("/"),
    API_TIMEOUT=float(os.getenv("API_TIMEOUT", "5")),
    PORT=int(os.getenv("FRONTEND_PORT", "21001")),
    HOST=os.getenv("FRONTEND_HOST", "127.0.0.1"),
    DEBUG=os.getenv("FLASK_DEBUG", "false").lower() == "true",
)


class StoreAPIError(Exception):
    """A readable error returned while talking to the bookstore backend."""


def api_request(method: str, path: str, **kwargs):
    """Send requests from Flask to FastAPI, with a safe error message for users."""
    try:
        response = requests.request(
            method,
            app.config["API_URL"] + path,
            timeout=app.config["API_TIMEOUT"],
            **kwargs,
        )
        if not response.ok:
            try:
                detail = response.json().get(
                    "detail", "The server could not complete the request."
                )
            except (ValueError, AttributeError, TypeError):
                detail = "The server could not complete the request."
            if isinstance(detail, list):
                fields = [
                    ".".join(str(x) for x in error.get("loc", [])[1:]) or "Field"
                    for error in detail
                    if isinstance(error, dict)
                ]
                detail = "Please check these fields: " + ", ".join(fields[:6])
            raise StoreAPIError(str(detail))
        if response.status_code == 204:
            return None
        return response.json()
    except requests.RequestException as exc:
        logger.warning("Bookstore API unavailable: %s", exc)
        raise StoreAPIError(
            "The bookstore API is unavailable. Start the backend and try again."
        ) from exc


def get_books() -> list[dict]:
    return api_request("GET", "/books")


def create_book(payload: dict) -> dict:
    return api_request("POST", "/books", json=payload)


def update_book(book_id: str, payload: dict) -> dict:
    return api_request("PUT", f"/books/{book_id}", json=payload)


def delete_book(book_id: str) -> None:
    api_request("DELETE", f"/books/{book_id}")


@app.context_processor
def supply_csrf_token():
    if session.get("csrf_token") is None:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return {"csrf_token": session["csrf_token"]}


def require_csrf() -> None:
    expected = session.get("csrf_token", "")
    supplied = request.form.get("csrf_token", "")
    if not expected or not hmac.compare_digest(expected, supplied):
        abort(400, "Invalid form token. Refresh the page and try again.")


def form_to_payload() -> dict:
    """Leave number parsing/constraint checking to the Pydantic API models."""
    return {
        "title": request.form.get("title", "").strip(),
        "author": request.form.get("author", "").strip(),
        "genre": request.form.get("genre", "").strip(),
        "isbn": request.form.get("isbn", "").strip() or None,
        "price": request.form.get("price", ""),
        "quantity": request.form.get("quantity", ""),
        "description": request.form.get("description", "").strip(),
    }


@app.template_filter("money")
def format_money(value: object) -> str:
    return f"${Decimal(str(value)):,.2f}"


@app.get("/")
def index():
    query = request.args.get("q", "").strip()[:160]
    genre = request.args.get("genre", "").strip()[:60]
    books: list[dict] = []
    genres: list[str] = []
    stats = {
        "total_titles": 0,
        "total_copies": 0,
        "inventory_value": "0.00",
        "low_stock_titles": 0,
    }
    api_error = None
    try:
        catalog = get_books()
        genres = sorted({book["genre"] for book in catalog}, key=str.casefold)
        books = [
            book
            for book in catalog
            if (
                not query
                or query.casefold()
                in " ".join(
                    [book["title"], book["author"], book.get("isbn") or ""]
                ).casefold()
            )
            and (not genre or book["genre"].casefold() == genre.casefold())
        ]
        stats = api_request("GET", "/stats")
    except StoreAPIError as exc:
        api_error = str(exc)

    return render_template(
        "index.html",
        books=books,
        stats=stats,
        genres=genres,
        query=query,
        selected_genre=genre,
        api_error=api_error,
    )


@app.post("/books")
def add_book():
    require_csrf()
    try:
        create_book(form_to_payload())
        flash("Book added to your collection.", "success")
    except StoreAPIError as exc:
        flash(f"Could not add book: {exc}", "error")
    return redirect(url_for("index"))


@app.post("/books/<uuid:book_id>/edit")
def edit_book(book_id: UUID):
    require_csrf()
    try:
        update_book(str(book_id), form_to_payload())
        flash("Book details saved successfully.", "success")
    except StoreAPIError as exc:
        flash(f"Could not update book: {exc}", "error")
    return redirect(url_for("index"))


@app.post("/books/<uuid:book_id>/delete")
def remove_book(book_id: UUID):
    require_csrf()
    try:
        delete_book(str(book_id))
        flash("Book removed from your collection.", "success")
    except StoreAPIError as exc:
        flash(f"Could not delete book: {exc}", "error")
    return redirect(url_for("index"))


@app.get("/health")
def health():
    try:
        api_request("GET", "/health")
        return jsonify(status="healthy", api_connectivity=True)
    except StoreAPIError:
        return jsonify(status="unhealthy", api_connectivity=False), 503


def main():
    logger.info("Starting Leaf & Lore Bookstore UI")
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"])


if __name__ == "__main__":
    main()
