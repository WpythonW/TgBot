# handlers_start.py

from aiogram import types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from database import db
from keyboards import get_main_keyboard, get_inline_keyboard
from aiogram.types import Message
from handlers_user_input import update_user_data, show_current_data, show_registration_number, cancel_participation
import logging
from config import CHANNEL_NAME

async def cmd_start(message: Message, state: FSMContext):
    logging.info(f"Start command received from user {message.from_user.id}")
    user_id = message.from_user.id
    user_data = await db.db_operation('select', user_id=user_id)
    if not user_data:
        await db.db_operation('insert', user_id=user_id)
        user_data = (user_id, None, None, None, None, None, None, None)
    
    user_dict = {
        'email': user_data[1] if user_data else None, 
        'city': user_data[2] if user_data else None, 
        'post_link': user_data[3] if user_data else None, 
        'phone': user_data[4] if user_data else None,
        'name': user_data[5] if user_data else None,
        'company': user_data[6] if user_data else None,
        'position': user_data[7] if user_data else None
    }
    
    await state.set_data(user_dict)
    
    welcome_text = ("Привет! Это бот по розыгрышу скутера. 🛵\n\n"
                    f"Для участия в розыгрыше необходимо подписаться на канал {CHANNEL_NAME} и заполнить следующие данные:\n"
                    "- Имя\n"
                    "- Электронная почта\n"
                    "- Город\n"
                    "- Ссылка на пост\n"
                    "- Номер телефона\n"
                    "- Название компании\n"
                    "- Должность\n\n"
                    "Выберите данные для ввода или изменения. Учтите, что при розыгрыше будет проверяться выполнение всех пунктов, в том числе, пункт 3 (публикация фото скутера)")
    
    await message.answer(welcome_text)
    logging.info(f"Welcome message sent to user {message.from_user.id}")
    
    await update_user_data(message, state)

def register_handlers_start(dp):
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(show_registration_number, Command("number"))
    dp.message.register(show_current_data, Command("mydata"))
    dp.message.register(cancel_participation, Command("cancel"))
