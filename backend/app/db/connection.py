import psycopg2
from psycopg2.extras import RealDictCursor

from app.core.config import settings

_conn = None


def get_connection():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(settings.DATABASE_URL)
        _conn.autocommit = True
    return _conn


def query(sql: str, params: tuple | None = None) -> list[dict]:
    conn = get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]


def execute(sql: str, params: tuple | None = None) -> None:
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(sql, params)
