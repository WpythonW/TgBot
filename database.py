# database.py

import aiosqlite
import asyncio
import os
from config import DB_HOST, DB_PATH, DB_PORT

async def db_operation(operation, user_id=None, email=None, city=None, post_link=None, phone=None, name=None, company=None, position=None):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            print(f"Successfully connected to database for operation: {operation}")
        print(f"Данные: user_id={user_id}, email={email}, city={city}, post_link={post_link}, phone={phone}, name={name}, company={company}, position={position}")
        
        if operation == 'update':
            updates = []
            params = []
            for field, value in [('email', email), ('city', city), ('post_link', post_link), ('phone', phone), ('name', name), ('company', company), ('position', position)]:
                updates.append(f"{field} = ?")
                params.append(value)
            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
                print(f"SQL запрос: {query}")
                print(f"Параметры: {params}")
                await db.execute(query, params)
                await db.commit()
            else:
                print("Нет данных для обновления")
        
        elif operation == 'select':
            query = "SELECT * FROM users WHERE user_id = ?"
            async with db.execute(query, (user_id,)) as cursor:
                return await cursor.fetchone()
        
        elif operation == 'insert':
            query = "INSERT INTO users (user_id, email, city, post_link, phone, name, company, position) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            await db.execute(query, (user_id, email, city, post_link, phone, name, company, position))
        
        elif operation == 'get_or_create_registration_number':
            async with db.execute("SELECT registration_number FROM users WHERE user_id = ?", (user_id,)) as cursor:
                result = await cursor.fetchone()
            if result and result[0]:
                return result[0]
            else:
                async with db.execute("SELECT MAX(registration_number) FROM users") as cursor:
                    result = await cursor.fetchone()
                max_number = result[0] if result and result[0] is not None else 0
                new_number = max_number + 1
                await db.execute("UPDATE users SET registration_number = ? WHERE user_id = ?", (new_number, user_id))
                await db.commit()  # Добавьте эту строку
                return new_number
        
        await db.commit()
    except Exception as e:
        print(f"Error in db_operation: {e}")
        raise
        
async def create_table():
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            print("Successfully connected to database for create_table")
            await db.execute('''
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
            await db.commit()
            print("Table created successfully")
    except Exception as e:
        print(f"Error in create_table: {e}")
        raise