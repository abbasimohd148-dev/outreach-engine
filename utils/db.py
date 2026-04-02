import asyncpg
import os

pool = None


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
    global pool

    if pool is None:
        pool = await asyncpg.create_pool(
            os.getenv("DATABASE_URL")
        )

    return Database(pool)