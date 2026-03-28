"""Run database migrations.

Usage:
    python -m app.db.migrate
"""

import pathlib

from app.db.connection import get_connection

MIGRATIONS_DIR = pathlib.Path(__file__).parent / "migrations"


def run_migrations():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()

        cur.execute("SELECT filename FROM _migrations ORDER BY id")
        applied = {row[0] for row in cur.fetchall()}

    sql_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for f in sql_files:
        if f.name in applied:
            continue
        print(f"Applying migration: {f.name}")
        sql = f.read_text()
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO _migrations (filename) VALUES (%s)", (f.name,)
            )
        conn.commit()
        print(f"  Done: {f.name}")

    print("All migrations applied.")


if __name__ == "__main__":
    run_migrations()
