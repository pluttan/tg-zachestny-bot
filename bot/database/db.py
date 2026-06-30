import aiosqlite
from database.models import SCHEMA


_db_path: str = "bot.db"
_connection: aiosqlite.Connection | None = None


async def init_db(db_path: str = "bot.db") -> aiosqlite.Connection:
    global _db_path, _connection
    _db_path = db_path
    _connection = await aiosqlite.connect(db_path)
    _connection.row_factory = aiosqlite.Row
    await _connection.executescript(SCHEMA)
    await _connection.commit()
    return _connection


async def get_db() -> aiosqlite.Connection:
    if _connection is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _connection


async def close_db():
    global _connection
    if _connection:
        await _connection.close()
        _connection = None
