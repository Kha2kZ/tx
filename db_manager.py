import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        self.create_tables()

    def create_tables(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    discord_id TEXT NOT NULL UNIQUE,
                    username TEXT NOT NULL,
                    balance BIGINT DEFAULT 0 NOT NULL,
                    daily_streak INTEGER DEFAULT 0 NOT NULL,
                    last_daily TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE NOT NULL
                );
            """)
            self.conn.commit()

    def get_user(self, discord_id):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE discord_id = %s", (discord_id,))
            return cur.fetchone()

    def create_user(self, discord_id, username):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "INSERT INTO users (discord_id, username) VALUES (%s, %s) RETURNING *",
                (discord_id, username)
            )
            self.conn.commit()
            return cur.fetchone()

    def update_user(self, discord_id, **kwargs):
        if not kwargs:
            return
        fields = ", ".join([f"{k} = %s" for k in kwargs.keys()])
        values = list(kwargs.values()) + [discord_id]
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"UPDATE users SET {fields} WHERE discord_id = %s RETURNING *", values)
            self.conn.commit()
            return cur.fetchone()

    def get_top_users(self, limit=10):
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users ORDER BY balance DESC LIMIT %s", (limit,))
            return cur.fetchall()

db = DatabaseManager()
