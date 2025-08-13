import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            user='admin',
            password='secret',
            database='inventory',
            host='db',
            port=5432
        )
        print("Successfully connected to the database!")
        await conn.close()
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())