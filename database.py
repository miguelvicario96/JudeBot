import os
import psycopg2
import psycopg2.extras
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
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


def add_expense(description: str, amount: float, category: str) -> int:
    date = datetime.now().isoformat()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO expenses (description, amount, category, date) "
                "VALUES (%s, %s, %s, %s) RETURNING id",
                (description, amount, category, date),
            )
            row = cur.fetchone()
        conn.commit()
    return row[0]


def get_expenses_by_month(year: int, month: int) -> list:
    prefix = f"{year}-{month:02d}"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM expenses WHERE date LIKE %s ORDER BY date DESC",
                (f"{prefix}%",),
            )
            return [dict(r) for r in cur.fetchall()]


def get_totals_by_category(year: int, month: int) -> list:
    prefix = f"{year}-{month:02d}"
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
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
            return [dict(r) for r in cur.fetchall()]


def get_last_expenses(limit: int = 10) -> list:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM expenses ORDER BY date DESC LIMIT %s",
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_all_expenses_summary() -> dict:
    """Historical stats used to enrich the AI prompt."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses")
            total = float(cur.fetchone()["total"])

            cur.execute(
                "SELECT COUNT(DISTINCT LEFT(date, 7)) AS months FROM expenses"
            )
            months = cur.fetchone()["months"] or 1

            cur.execute(
                """
                SELECT category, SUM(amount) AS total
                FROM expenses
                GROUP BY category
                ORDER BY total DESC
                """
            )
            by_category = [dict(r) for r in cur.fetchall()]

            cur.execute(
                """
                SELECT description, amount, category, date
                FROM expenses
                ORDER BY amount DESC
                LIMIT 5
                """
            )
            top_expenses = [dict(r) for r in cur.fetchall()]

    return {
        "total": total,
        "monthly_avg": total / months,
        "months": months,
        "by_category": by_category,
        "top_expenses": top_expenses,
    }


def delete_expense(expense_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
            deleted = cur.rowcount
        conn.commit()
    return deleted > 0
