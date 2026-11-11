"""Environment-based configuration for the bookstore API."""

import os
from pathlib import Path

APP_NAME = os.getenv("APP_NAME", "Leaf & Lore Bookstore API")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "21002"))
DATA_DIR = Path(
    os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data"))
)
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "5"))


def parse_list_env(env_name: str, default: str) -> list[str]:
    value = os.getenv(env_name, default)
    return [part.strip() for part in value.split(",") if part.strip()]


CORS_ALLOW_ORIGINS = parse_list_env(
    "CORS_ALLOW_ORIGINS", "http://localhost:21001,http://127.0.0.1:21001"
)
CORS_ALLOW_METHODS = parse_list_env("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE")
CORS_ALLOW_HEADERS = parse_list_env("CORS_ALLOW_HEADERS", "Content-Type,Authorization")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() == "true"
