import asyncpg
from datetime import datetime
from typing import Optional, Dict, List
import os
import shutil

from utils.config import Config

_db_pool: Optional[asyncpg.Pool] = None


# ====================== DATABASE CONNECTION ====================== #
async def get_pool() -> asyncpg.Pool:
    """Ensure a connection pool exists"""
    global _db_pool
    if _db_pool is None:
        _db_pool = await asyncpg.create_pool(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            min_size=1,
            max_size=5
        )
    return _db_pool


# ====================== TICKET MANAGER ====================== #
class TicketManager:
    """Handles all ticket-related database operations"""

    @staticmethod
    async def init_db():
        """Initialize the tickets table"""
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL UNIQUE,
                    ticket_number INTEGER NOT NULL,
                    claimed_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    closed_by BIGINT,
                    status TEXT DEFAULT 'open',
                    UNIQUE(guild_id, user_id, status)
                );
            """)
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS ticket_settings (
                guild_id BIGINT PRIMARY KEY,
                manager_role_id BIGINT,
                log_channel_id BIGINT
               );
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_guild_user ON tickets(guild_id, user_id, status);")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_channel ON tickets(channel_id);")

    @staticmethod
    async def create_ticket(guild_id: int, user_id: int, channel_id: int, ticket_number: int) -> int:
        """Create a new ticket"""
        pool = await get_pool()
        async with pool.acquire() as conn:
            result = await conn.fetchrow("""
                INSERT INTO tickets (guild_id, user_id, channel_id, ticket_number)
                VALUES ($1, $2, $3, $4)
                RETURNING id;
            """, guild_id, user_id, channel_id, ticket_number)
            return result["id"]

    @staticmethod
    async def get_ticket_by_channel(channel_id: int) -> Optional[Dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM tickets WHERE channel_id = $1 AND status = 'open';
            """, channel_id)
            return dict(row) if row else None

    @staticmethod
    async def get_user_ticket(guild_id: int, user_id: int) -> Optional[Dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM tickets WHERE guild_id = $1 AND user_id = $2 AND status = 'open';
            """, guild_id, user_id)
            return dict(row) if row else None

    @staticmethod
    async def get_ticket_count(guild_id: int) -> int:
        pool = await get_pool()
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE guild_id = $1;", guild_id)
            return count or 0

    @staticmethod
    async def claim_ticket(channel_id: int, user_id: int):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("UPDATE tickets SET claimed_by = $1 WHERE channel_id = $2;", user_id, channel_id)

    @staticmethod
    async def close_ticket(channel_id: int, closed_by: int):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                UPDATE tickets 
                SET status = 'closed', closed_at = CURRENT_TIMESTAMP, closed_by = $1
                WHERE channel_id = $2;
            """, closed_by, channel_id)

    @staticmethod
    async def get_open_tickets(guild_id: int) -> List[Dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM tickets WHERE guild_id = $1 AND status = 'open'
                ORDER BY created_at DESC;
            """, guild_id)
            return [dict(row) for row in rows]

    @staticmethod
    async def get_ticket_stats(guild_id: int) -> Dict:
        pool = await get_pool()
        async with pool.acquire() as conn:
            total = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE guild_id = $1;", guild_id)
            open_count = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE guild_id = $1 AND status = 'open';", guild_id)
            closed = await conn.fetchval("SELECT COUNT(*) FROM tickets WHERE guild_id = $1 AND status = 'closed';", guild_id)
            return {"total": total or 0, "open": open_count or 0, "closed": closed or 0}
    
    @staticmethod
    async def save_settings(guild_id: int, manager_role_id: int, log_channel_id: int):
        pool = await get_pool()
        async with pool.acquire() as conn:
         await conn.execute("""
            INSERT INTO ticket_settings (guild_id, manager_role_id, log_channel_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (guild_id)
            DO UPDATE SET 
                manager_role_id = EXCLUDED.manager_role_id,
                log_channel_id = EXCLUDED.log_channel_id;""", guild_id, manager_role_id, log_channel_id)

    @staticmethod
    async def load_settings(guild_id: int):
        pool = await get_pool()
        async with pool.acquire() as conn:
         row = await conn.fetchrow("""
            SELECT manager_role_id, log_channel_id
            FROM ticket_settings
            WHERE guild_id = $1;""", guild_id)
        return dict(row) if row else None


# ====================== WELCOME MANAGER ====================== #
class WelcomeManager:
    """Handles all welcome/goodbye related database operations"""

    @staticmethod
    async def init_db():
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS welcome_settings (
                    guild_id BIGINT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    channel_id BIGINT,
                    message TEXT,
                    auto_role_id BIGINT,
                    show_buttons BOOLEAN DEFAULT TRUE,
                    auto_delete_after INTEGER,
                    goodbye_enabled BOOLEAN DEFAULT FALSE,
                    goodbye_channel_id BIGINT,
                    goodbye_message TEXT,
                    title TEXT,
                    description TEXT,
                    footer TEXT,
                    thumbnail TEXT,
                    image TEXT,
                    footer_icon TEXT,
                    color TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    @staticmethod
    async def get_settings(guild_id: int) -> Optional[Dict]:
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM welcome_settings WHERE guild_id = $1;", guild_id)
            return dict(row) if row else None

    @staticmethod
    async def update_settings(guild_id: int, **kwargs):
        pool = await get_pool()
        async with pool.acquire() as conn:
            existing = await conn.fetchval("SELECT guild_id FROM welcome_settings WHERE guild_id = $1;", guild_id)

            if existing:
                fields = [f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())]
                query = f"""
                    UPDATE welcome_settings
                    SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE guild_id = $1;
                """
                await conn.execute(query, guild_id, *kwargs.values())
            else:
                columns = ["guild_id"] + list(kwargs.keys())
                values = [guild_id] + list(kwargs.values())
                placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
                query = f"""
                    INSERT INTO welcome_settings ({', '.join(columns)})
                    VALUES ({placeholders});
                """
                await conn.execute(query, *values)

    @staticmethod
    async def delete_settings(guild_id: int):
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM welcome_settings WHERE guild_id = $1;", guild_id)


# ====================== UTILITIES ====================== #
async def ensure_database_exists():
    pool = await get_pool()
    await TicketManager.init_db()
    await WelcomeManager.init_db()
    print("✅ PostgreSQL Database initialized successfully!")


async def get_guild_data(guild_id: int) -> Dict:
    return {
        "tickets": {
            "open": await TicketManager.get_open_tickets(guild_id),
            "stats": await TicketManager.get_ticket_stats(guild_id)
        },
        "welcome": await WelcomeManager.get_settings(guild_id)
    }
