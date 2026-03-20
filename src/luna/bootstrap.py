import asyncio

from luna.core.database import Base
from luna.core.database import engine
from luna.seed import seed


async def bootstrap() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await seed()


def main() -> None:
    asyncio.run(bootstrap())


if __name__ == "__main__":
    main()
