import asyncpg
import uuid
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def init_teddi_db(dsn: str):
    """Initialize the database connection pool."""
    global _pool
    if not _pool:
        try:
            _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)
            logger.info("✅ TEDDI Labs: Database pool initialized.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database pool: {e}")
            raise e


async def close_teddi_db():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("🔒 TEDDI Labs: Database pool closed.")


async def get_db_pool():
    """Return the database pool. Must be called after initialization."""
    global _pool
    if _pool is None:
        raise Exception("Database pool not initialized")
    return _pool


async def pop_teddi_entropy():
    """Pop one unused quantum seed."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            WITH next_entropy AS (
                SELECT id, raw_hex
                FROM quantum_pool
                WHERE used = false
                ORDER BY created_at ASC
                LIMIT 1
                FOR UPDATE SKIP LOCKED
            )
            UPDATE quantum_pool
            SET used = true
            FROM next_entropy
            WHERE quantum_pool.id = next_entropy.id
            RETURNING quantum_pool.id, next_entropy.raw_hex;
            """
        )
        if not row:
            raise Exception("TEDDI Quantum Buffer is depleted. Admin /refill required.")
        return row["id"], row["raw_hex"]


async def bulk_insert_teddi_entropy(hex_blocks: List[str]) -> int:
    """Insert multiple quantum seeds."""
    pool = await get_db_pool()
    records = [(str(uuid.uuid4()), h) for h in hex_blocks]
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                "INSERT INTO quantum_pool (id, raw_hex) VALUES ($1, $2)",
                records
            )
    return len(records)


async def get_pool_dependency():
    """Dependency that provides the database pool to routes."""
    return await get_db_pool()