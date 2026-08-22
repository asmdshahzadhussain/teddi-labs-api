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


async def get_pool():
    """Return the database pool (for dependency injection)."""
    return _pool


async def pop_teddi_entropy():
    """
    TEDDI Atomic Pop: Fetches one unused quantum block, locks it instantly,
    and marks it as consumed. Handles 100+ concurrent requests with zero collisions.
    """
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
    """TEDDI Bulk Loader: Efficiently inserts 100 fresh quantum seeds."""
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
    """Check if an API key exists and is active in the database."""
    if _pool is None:
        logger.warning("⚠️ Database pool not initialized when validating API key")
        return False
    
    try:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT key_string FROM api_keys WHERE key_string = $1 AND is_active = true",
                key
            )
            return row is not None
    except Exception as e:
        logger.error(f"❌ Error validating API key: {e}")
        return False


async def get_key_details(key: str):
    """Fetch all details for a given API key."""
    if _pool is None:
        raise Exception("TEDDI: Database pool not initialized")
    
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT key_string, client_name, is_active, expires_at, 
                   monthly_limit, usage_count, last_reset_at
            FROM api_keys 
            WHERE key_string = $1
            """,
            key
        )
        return row


async def increment_usage(key: str) -> int:
    """Increment usage count for a given API key and return the new count."""
    if _pool is None:
        raise Exception("TEDDI: Database pool not initialized")
    
    async with _pool.acquire() as conn:
        result = await conn.fetchrow(
            "UPDATE api_keys SET usage_count = usage_count + 1 WHERE key_string = $1 RETURNING usage_count",
            key
        )
        return result["usage_count"] if result else 0


async def reset_usage(key: str):
    """Reset usage count for a given API key (called monthly)."""
    if _pool is None:
        raise Exception("TEDDI: Database pool not initialized")
    
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE api_keys SET usage_count = 0, last_reset_at = NOW() WHERE key_string = $1",
            key
        )


async def create_api_key(client_name: str) -> str:
    """Create a new API key with default Pro limits."""
    if _pool is None:
        raise Exception("TEDDI: Database pool not initialized")
    
    import secrets
    import string
    
    alphabet = string.ascii_uppercase + string.digits
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(8))
    new_key = f"TEDDI_PROD_{random_suffix}"
    
    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO api_keys (key_string, client_name, is_active, monthly_limit, expires_at)
            VALUES ($1, $2, true, 5000, NOW() + INTERVAL '30 days')
            """,
            new_key, client_name
        )
    
    return new_key