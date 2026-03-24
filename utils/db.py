import asyncpg
import os


class Database:
    def __init__(self, pool):
        self.pool = pool

    async def fetch(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)


async def get_db():
    pool = await asyncpg.create_pool(
        os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/outreach_engine"
        )
    )

    return Database(pool)