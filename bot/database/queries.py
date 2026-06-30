import json
from datetime import datetime, timedelta
import aiosqlite


async def get_or_create_user(
    db: aiosqlite.Connection, tg_id: int, username: str | None, full_name: str | None
) -> dict:
    cursor = await db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = await cursor.fetchone()
    if row:
        return dict(row)
    await db.execute(
        "INSERT INTO users (tg_id, username, full_name) VALUES (?, ?, ?)",
        (tg_id, username, full_name),
    )
    await db.commit()
    cursor = await db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,))
    row = await cursor.fetchone()
    return dict(row)


async def save_check(
    db: aiosqlite.Connection,
    tg_id: int,
    check_type: str,
    query: str,
    result: dict,
    cost: float,
) -> int:
    cursor = await db.execute(
        "INSERT INTO checks (tg_id, check_type, query, result, cost) VALUES (?, ?, ?, ?, ?)",
        (tg_id, check_type, query, json.dumps(result, ensure_ascii=False), cost),
    )
    await db.commit()
    return cursor.lastrowid


async def get_check_by_id(db: aiosqlite.Connection, check_id: int) -> dict | None:
    cursor = await db.execute("SELECT * FROM checks WHERE id = ?", (check_id,))
    row = await cursor.fetchone()
    if row:
        data = dict(row)
        data["result"] = json.loads(data["result"])
        return data
    return None


async def get_checks_history(
    db: aiosqlite.Connection, tg_id: int, limit: int = 10
) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM checks WHERE tg_id = ? ORDER BY created_at DESC LIMIT ?",
        (tg_id, limit),
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        data = dict(row)
        data["result"] = json.loads(data["result"])
        result.append(data)
    return result


async def get_all_users(
    db: aiosqlite.Connection, offset: int = 0, limit: int = 20
) -> list[dict]:
    cursor = await db.execute(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def get_user_count(db: aiosqlite.Connection) -> int:
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    row = await cursor.fetchone()
    return row["cnt"]


async def get_stats(db: aiosqlite.Connection, period: str = "day") -> dict:
    now = datetime.now()
    if period == "day":
        since = now - timedelta(days=1)
    elif period == "week":
        since = now - timedelta(weeks=1)
    elif period == "month":
        since = now - timedelta(days=30)
    else:
        since = datetime.min

    since_str = since.strftime("%Y-%m-%d %H:%M:%S")

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    total_users = (await cursor.fetchone())["cnt"]

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE created_at >= ?", (since_str,)
    )
    new_users = (await cursor.fetchone())["cnt"]

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM checks WHERE created_at >= ?", (since_str,)
    )
    checks_count = (await cursor.fetchone())["cnt"]

    cursor = await db.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'succeeded' AND created_at >= ?",
        (since_str,),
    )
    payments_sum = (await cursor.fetchone())["total"]

    return {
        "period": period,
        "total_users": total_users,
        "new_users": new_users,
        "checks_count": checks_count,
        "payments_sum": float(payments_sum),
    }


async def get_all_tg_ids(db: aiosqlite.Connection) -> list[int]:
    cursor = await db.execute("SELECT tg_id FROM users")
    rows = await cursor.fetchall()
    return [row["tg_id"] for row in rows]


# === Payments ===


async def create_payment(
    db: aiosqlite.Connection,
    tg_id: int,
    amount: float,
    payment_id: str,
    check_type: str,
) -> int:
    cursor = await db.execute(
        "INSERT INTO payments (tg_id, amount, payment_id, status, check_type) "
        "VALUES (?, ?, ?, 'pending', ?)",
        (tg_id, amount, payment_id, check_type),
    )
    await db.commit()
    return cursor.lastrowid


async def update_payment_status(
    db: aiosqlite.Connection, payment_id: str, status: str
):
    await db.execute(
        "UPDATE payments SET status = ? WHERE payment_id = ?", (status, payment_id)
    )
    await db.commit()


async def get_payment_by_id(
    db: aiosqlite.Connection, payment_id: str
) -> dict | None:
    cursor = await db.execute(
        "SELECT * FROM payments WHERE payment_id = ?", (payment_id,)
    )
    row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def get_paid_unused_payment(
    db: aiosqlite.Connection, tg_id: int
) -> dict | None:
    """Найти оплаченный, но не использованный платёж (ожидает ввода данных)."""
    cursor = await db.execute(
        "SELECT * FROM payments WHERE tg_id = ? AND status = 'paid' "
        "ORDER BY created_at DESC LIMIT 1",
        (tg_id,),
    )
    row = await cursor.fetchone()
    if row:
        return dict(row)
    return None


async def set_payment_query_and_complete(
    db: aiosqlite.Connection, payment_id: str, check_query: str
):
    """Записать запрос и пометить платёж как использованный."""
    await db.execute(
        "UPDATE payments SET check_query = ?, status = 'succeeded' WHERE payment_id = ?",
        (check_query, payment_id),
    )
    await db.commit()
