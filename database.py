import aiosqlite
import asyncio, logging
from config import DB_PATH

class Database:
    def __init__(self):
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(DB_PATH)
        await self.create_table()

    async def close(self):
        if self.db:
            await self.db.close()

    async def create_table(self):
        await self.db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            email TEXT,
            city TEXT,
            post_link TEXT,
            phone TEXT,
            name TEXT,
            company TEXT,
            position TEXT,
            registration_number INTEGER
        )
        ''')
        await self.db.commit()

    async def db_operation(self, operation, user_id=None, email=None, city=None, post_link=None, phone=None, name=None, company=None, position=None, registration_number=None):
        try:
            if operation == 'update':
                query = """
                UPDATE users 
                SET email = ?, city = ?, post_link = ?, phone = ?, name = ?, company = ?, position = ?, registration_number = ?
                WHERE user_id = ?
                """
                params = (email, city, post_link, phone, name, company, position, registration_number, user_id)
                await self.db.execute(query, params)
                await self.db.commit()
                logging.info(f"Update operation completed for user {user_id}")
            
            elif operation == 'select':
                query = "SELECT * FROM users WHERE user_id = ?"
                async with self.db.execute(query, (user_id,)) as cursor:
                    result = await cursor.fetchone()
                    logging.info(f"Select operation result for user {user_id}: {result}")
                    return result
            
            elif operation == 'insert':
                query = """
                INSERT OR REPLACE INTO users 
                (user_id, email, city, post_link, phone, name, company, position, registration_number) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = (user_id, email, city, post_link, phone, name, company, position, registration_number)
                await self.db.execute(query, params)
                await self.db.commit()
                logging.info(f"Insert operation completed for user {user_id}")
            
            elif operation == 'get_or_create_registration_number':
                async with self.db.execute("SELECT registration_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
                    result = await cursor.fetchone()
                if result and result[0]:
                    return result[0]
                else:
                    async with self.db.execute("SELECT MAX(registration_number) FROM users") as cursor:
                        result = await cursor.fetchone()
                    max_number = result[0] if result and result[0] is not None else 0
                    new_number = max_number + 1
                    await self.db.execute("UPDATE users SET registration_number = ? WHERE user_id = ?", (new_number, user_id))
                    await self.db.commit()
                    return new_number
        
        except Exception as e:
            logging.error(f"Error in db_operation: {e}")
            raise

db = Database()

async def init_db():
    await db.connect()

async def close_db():
    await db.close()