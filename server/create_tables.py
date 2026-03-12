#!/usr/bin/env python3
"""Script to create database tables."""

import asyncio
from database.engine import engine
from database.models import Base


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully!")


if __name__ == "__main__":
    asyncio.run(create_tables())
