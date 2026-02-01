import aiosqlite
import time

DB_NAME = "bot.db"


async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                referrer_id INTEGER,
                reg_date REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name TEXT,
                modifier TEXT,
                final_price INTEGER
            )
        """)
        await db.commit()


async def add_user(user_id, username, referrer_id=None, start_balance=0):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute(
                "INSERT INTO users (user_id, username, balance, referrer_id, reg_date) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, start_balance, referrer_id, time.time())
            )
            await db.commit()
            return True
        except aiosqlite.IntegrityError:
            return False


async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()


async def get_user_by_username(username):
    """Поиск пользователя по юзернейму (без учета регистра)"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users WHERE LOWER(username) = LOWER(?)", (username,)) as cursor:
            return await cursor.fetchone()


async def update_balance(user_id, amount):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        await db.commit()


async def add_item(user_id, name, mod, price):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO inventory (user_id, name, modifier, final_price) VALUES (?, ?, ?, ?)",
                         (user_id, name, mod, price))
        await db.commit()


async def get_inventory(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT name, modifier, final_price FROM inventory WHERE user_id = ?",
                              (user_id,)) as cursor:
            return await cursor.fetchall()


async def sell_all(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT SUM(final_price) FROM inventory WHERE user_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            total = res[0] if res[0] else 0
        await db.execute("DELETE FROM inventory WHERE user_id = ?", (user_id,))
        if total > 0:
            await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (total, user_id))
        await db.commit()
        return total


async def get_top(limit=10):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id, username, balance FROM users ORDER BY balance DESC LIMIT ?",
                              (limit,)) as cursor:
            return await cursor.fetchall()


async def get_referrals_count(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,)) as cursor:
            res = await cursor.fetchone()
            return res[0]


# Для админки
async def get_all_users():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            return await cursor.fetchall()


async def get_stats():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*), SUM(balance) FROM users") as cursor:
            return await cursor.fetchone()