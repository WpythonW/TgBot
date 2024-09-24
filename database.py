import aiosqlite
import asyncio
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

    async def db_operation(self, operation, user_id=None, email=None, city=None, post_link=None, phone=None, name=None, company=None, position=None):
        try:
            if operation == 'update':
                updates = []
                params = []
                for field, value in [('email', email), ('city', city), ('post_link', post_link), ('phone', phone), ('name', name), ('company', company), ('position', position)]:
                    if value is not None:
                        updates.append(f"{field} = ?")
                        params.append(value)
                if updates:
                    params.append(user_id)
                    query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                    await self.db.execute(query, params)
                    await self.db.commit()
            
            elif operation == 'select':
                query = "SELECT * FROM users WHERE user_id = ?"
                async with self.db.execute(query, (user_id,)) as cursor:
                    return await cursor.fetchone()
            
            elif operation == 'insert':
                query = "INSERT INTO users (user_id, email, city, post_link, phone, name, company, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                await self.db.execute(query, (user_id, email, city, post_link, phone, name, company, position))
                await self.db.commit()
            
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
            print(f"Error in db_operation: {e}")
            raise

db = Database()

async def init_db():
    await db.connect()

async def close_db():
    await db.close()