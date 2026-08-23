import asyncpg  # ✅ CORRECT — not asynccpp
import uuid
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None  # ✅ CORRECT


async def init_teddi_db(dsn: str):
    """Initialize the database connection pool."""
    global _pool
    if not _pool:
        _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10)  # ✅ CORRECT
        logger.info("✅ TEDDI Labs: Database pool initialized.")


async def close_teddi_db():
    """Close the database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        logger.info("🔒 TEDDI Labs: Database pool closed.")


async def pop_teddi_entropy():
    """Pop one unused quantum seed."""
    if _pool is None:
        raise Exception("TEDDI: Database pool not initialized")
    
    async with _pool.acquire() as conn:
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
    if _pool is None:
        raise Exception("TEDDI: Database pool not initialized")
    
    records = [(str(uuid.uuid4()), h) for h in hex_blocks]
    async with _pool.acquire() as conn:
        async with conn.transaction():
            await conn.executemany(
                "INSERT INTO quantum_pool (id, raw_hex) VALUES ($1, $2)",
                records
            )
    return len(records)


async def validate_api_key(key: str) -> bool:
    """Check if an API key exists and is active."""
    if _pool is None:
        return False
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT key_string FROM api_keys WHERE key_string = $1 AND is_active = true",
            key
        )
        return row is not None