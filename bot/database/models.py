SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    is_admin INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER REFERENCES users(tg_id),
    check_type TEXT CHECK(check_type IN ('ul', 'fl', 'ip')),
    query TEXT,
    result TEXT,
    cost REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER REFERENCES users(tg_id),
    amount REAL,
    payment_id TEXT UNIQUE,
    status TEXT CHECK(status IN ('pending', 'paid', 'succeeded', 'canceled')),
    check_type TEXT,
    check_query TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""
