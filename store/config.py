import os


def try_parse(type, value: str):
    try:
        return type(value)
    except Exception:
        return None


# Configuration for POSTGRES
POSTGRES_HOST = os.environ.get("POSTGRES_HOST") or "postgres_db"
POSTGRES_PORT = try_parse(int, os.environ.get("POSTGRES_PORT")) or 5432
POSTGRES_USER = os.environ.get("POSTGRES_USER") or "roma"
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD") or "tobeor"
POSTGRES_DB = os.environ.get("POSTGRES_DB") or "iot_db"
