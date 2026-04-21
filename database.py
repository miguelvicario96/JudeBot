import os
import ssl
import pg8000.dbapi
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

MEXICO_TZ = timezone(timedelta(hours=-6))

DATABASE_URL = os.getenv("DATABASE_URL")


def _parse_url(url_str: str) -> dict:
    u = urlparse(url_str)
    return {
        "host": u.hostname,
        "port": u.port or 5432,
        "database": u.path.lstrip("/"),
        "user": u.username,
        "password": u.password,
    }


def get_connection():
    p = _parse_url(DATABASE_URL)
    ssl_ctx = ssl.create_default_context()
    return pg8000.dbapi.connect(
        host=p["host"],
        port=p["port"],
        database=p["database"],
        user=p["user"],
        password=p["password"],
        ssl_context=ssl_ctx,
    )


def _to_dicts(cursor, rows: list) -> list:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in rows]


def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id          SERIAL PRIMARY KEY,
                description TEXT NOT NULL,
                amount      NUMERIC(10,2) NOT NULL,
                category    TEXT NOT NULL,
                date        TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def add_expense(description: str, amount: float, category: str) -> int:
    date = datetime.now(MEXICO_TZ).isoformat()
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO expenses (description, amount, category, date) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (description, amount, category, date),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0]
    finally:
        conn.close()


def get_expenses_by_month(year: int, month: int) -> list:
    prefix = f"{year}-{month:02d}"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM expenses WHERE date LIKE %s ORDER BY date DESC",
            (f"{prefix}%",),
        )
        return _to_dicts(cur, cur.fetchall())
    finally:
        conn.close()


def get_totals_by_category(year: int, month: int) -> list:
    prefix = f"{year}-{month:02d}"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT category, SUM(amount) AS total, COUNT(*) AS count
            FROM expenses
            WHERE date LIKE %s
            GROUP BY category
            ORDER BY total DESC
            """,
            (f"{prefix}%",),
        )
        return _to_dicts(cur, cur.fetchall())
    finally:
        conn.close()


def get_last_expenses(limit: int = 10) -> list:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM expenses ORDER BY date DESC LIMIT %s",
            (limit,),
        )
        return _to_dicts(cur, cur.fetchall())
    finally:
        conn.close()


def get_all_expenses_summary() -> dict:
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total = float(cur.fetchone()[0])

        cur.execute("SELECT COUNT(DISTINCT LEFT(date, 7)) FROM expenses")
        months = cur.fetchone()[0] or 1

        cur.execute(
            """
            SELECT category, SUM(amount) AS total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            """
        )
        by_category = _to_dicts(cur, cur.fetchall())

        cur.execute(
            """
            SELECT description, amount, category, date
            FROM expenses
            ORDER BY amount DESC
            LIMIT 5
            """
        )
        top_expenses = _to_dicts(cur, cur.fetchall())
    finally:
        conn.close()

    return {
        "total": total,
        "monthly_avg": total / months,
        "months": months,
        "by_category": by_category,
        "top_expenses": top_expenses,
    }


def update_category(expense_id: int, category: str) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE expenses SET category = %s WHERE id = %s",
            (category, expense_id),
        )
        updated = cur.rowcount
        conn.commit()
        return updated > 0
    finally:
        conn.close()


def delete_expense(expense_id: int) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
        deleted = cur.rowcount
        conn.commit()
        return deleted > 0
    finally:
        conn.close()
