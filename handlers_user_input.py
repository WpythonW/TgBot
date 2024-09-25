from aiogram import types, F
from aiogram.fsm.context import FSMContext
from database import db
from keyboards import get_inline_keyboard, get_main_keyboard, get_phone_keyboard, get_subscription_keyboard
from aiogram.types import Message, CallbackQuery
import json, logging
from config import CHANNEL_NAME
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def process_callback_input(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data
    logging.info(f"Получен callback: {action}")

    user_data = await state.get_data()
    input_message_id = user_data.get('input_message_id')

    # Удаляем предыдущее сообщение с запросом ввода, если оно существует
    if input_message_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, input_message_id)
        except Exception as e:
            logging.error(f"Ошибка при удалении предыдущего сообщения: {e}")

    if action.startswith("change_"):
        field = action[7:]
        logging.info(f"Изменяемое поле: {field}")
        if field == "phone":
            msg = await process_phone_share(callback_query.message, state)
            await state.update_data(input_message_id=msg.message_id, editing_field=field)
        else:
            field_names = {'email': 'почту', 'city': 'город', 'post_link': 'ссылку на пост', 'name': 'имя', 'company': 'название компании', 'position': 'должность'}
            if field in field_names:
                msg = await callback_query.message.answer(f"Пожалуйста, введите {field_names[field]}:")
                await state.update_data(input_message_id=msg.message_id, editing_field=field)
                logging.info(f"Запрошено изменение поля: {field}")
            else:
                await callback_query.answer("Неизвестное поле")
                logging.warning(f"Получено неизвестное поле: {field}")
    elif action == "send_data":
        # Проверяем, все ли поля заполнены
        #if all(user_data.get(field) for field in ['name', 'email', 'city', 'post_link', 'phone', 'company', 'position']):
        #    await request_subscription(callback_query, state)
        #else:
        #    await callback_query.answer("Пожалуйста, заполните все поля перед отправкой данных.", show_alert=True)
        await request_subscription(callback_query, state)
    elif action == "check_subscription":
        await save_data(callback_query, state)
    else:
        await callback_query.answer("Неизвестное действие")
    
    if action != "send_data":
        await callback_query.answer()


async def request_subscription(callback_query: CallbackQuery, state: FSMContext):
    keyboard = get_subscription_keyboard()
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

async def save_data(callback_query: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        user_id = callback_query.from_user.id
        db_data = {field: user_data.get(field) for field in ['name', 'email', 'city', 'post_link', 'phone', 'company', 'position']}
        
        # Получаем текущие данные пользователя из базы данных
        current_user_data = await db.db_operation('select', user_id=user_id)
        
        # Проверяем, есть ли у пользователя уже номер регистрации
        if current_user_data and current_user_data[8] is not None:
            registration_number = current_user_data[8]
        else:
            # Если номера нет, только тогда создаем новый
            registration_number = await db.db_operation('get_or_create_registration_number', user_id=user_id)
        
        # Добавляем registration_number к данным для обновления
        db_data['registration_number'] = registration_number
        
        # Обновляем данные пользователя
        await db.db_operation('update', user_id=user_id, **db_data)
        
        await callback_query.answer("Данные успешно сохранены!", show_alert=False)
        
        # Отправляем сообщение с порядковым номером
        await callback_query.message.answer(f"Ваши данные успешно обновлены.\nВаш порядковый номер: {registration_number}", reply_markup=get_main_keyboard())

        await callback_query.message.answer("Вы можете проверить свои данные или отменить участие.", reply_markup=get_main_keyboard())

    except Exception as e:
        print(f"Ошибка при сохранении данных: {e}")
        await callback_query.answer("Произошла ошибка при сохранении данных. Пожалуйста, попробуйте еще раз позже.", show_alert=True)


async def process_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    editing_field = user_data.get('editing_field')
    
    if editing_field:
        await state.update_data({editing_field: message.text})
        
        # Удаляем сообщение пользователя
        await message.delete()
        
        # Удаляем сообщение бота с запросом ввода
        input_message_id = user_data.get('input_message_id')
        if input_message_id:
            try:
                await message.bot.delete_message(message.chat.id, input_message_id)
            except Exception as e:
                logging.error(f"Ошибка при удалении сообщения бота: {e}")
        
        await update_user_data(message, state)
        await state.update_data(editing_field=None, input_message_id=None)


async def update_user_data(message: Message, state: FSMContext):
    user_data = await state.get_data()
    data_text = "Ваши текущие данные:\n"
    fields = {
        'name': 'Имя',
        'company': 'Компания',
        'position': 'Должность',
        'email': 'Email',
        'city': 'Город',
        'post_link': 'Ссылка на пост',
        'phone': 'Телефон'
    }
    for field, field_name in fields.items():
        value = user_data.get(field, 'Не заполнено')
        data_text += f"{field_name}: {value}\n"
    
    data_text += "\nПосле ввода всех данных не забудьте нажать 'Отправить данные'!"
    
    keyboard = get_inline_keyboard()
    
    data_message_id = user_data.get('data_message_id')
    try:
        if data_message_id:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=data_message_id,
                text=data_text,
                reply_markup=keyboard
            )
        else:
            new_message = await message.answer(data_text, reply_markup=keyboard)
            await state.update_data(data_message_id=new_message.message_id)
    except Exception as e:
        logging.error(f"Ошибка при обновлении/отправке сообщения: {e}")
        new_message = await message.answer(data_text, reply_markup=keyboard)
        await state.update_data(data_message_id=new_message.message_id)


async def show_current_data(message: Message, state: FSMContext):
    new_message = await message.answer("Загрузка данных...", reply_markup=get_main_keyboard())

    await state.update_data(data_message_id=new_message.message_id)
    await update_user_data(message, state)

async def process_phone_share(message: Message, state: FSMContext):
    keyboard = get_phone_keyboard()
    msg = await message.answer("Нажмите кнопку, чтобы поделиться номером телефона:", reply_markup=keyboard)
    await state.update_data(input_message_id=msg.message_id)
    return msg

async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone, editing_field=None)
    
    # Удаляем сообщение пользователя с контактом
    await message.delete()
    
    # Удаляем сообщение бота с запросом номера телефона
    user_data = await state.get_data()
    input_message_id = user_data.get('input_message_id')
    if input_message_id:
        try:
            await message.bot.delete_message(message.chat.id, input_message_id)
        except Exception as e:
            logging.error(f"Ошибка при удалении сообщения с запросом номера телефона: {e}")
    
    await update_user_data(message, state)
    await state.update_data(input_message_id=None)

# handlers_user_input.py
async def cancel_participation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    logging.info(f"Attempting to cancel participation for user {user_id}")
    
    # Удаляем данные пользователя из базы данных
    try:
        await db.db_operation('update', user_id=user_id, email=None, city=None, post_link=None, phone=None, name=None, company=None, position=None, registration_number=None)
        logging.info(f"Database update operation completed for user {user_id}")
    except Exception as e:
        logging.error(f"Error updating database for user {user_id}: {e}")
    
    # Очищаем состояние пользователя
    await state.clear()
    logging.info(f"State cleared for user {user_id}")
    
    # Удаляем сообщение с данными пользователя, если оно существует
    user_data = await state.get_data()
    data_message_id = user_data.get('data_message_id')
    if data_message_id:
        try:
            await message.bot.delete_message(message.chat.id, data_message_id)
            logging.info(f"Deleted data message for user {user_id}")
        except Exception as e:
            logging.error(f"Error deleting data message for user {user_id}: {e}")
    
    # Проверяем, что данные действительно удалены
    user_data = await db.db_operation('select', user_id=user_id)
    logging.info(f"User data after deletion attempt: {user_data}")
    if user_data and any(user_data[1:]):  # Проверяем все поля, кроме user_id
        logging.error(f"Data for user {user_id} was not fully deleted. Remaining data: {user_data}")
        await message.answer("Произошла ошибка при удалении данных. Пожалуйста, обратитесь к администратору.")
    else:
        logging.info(f"All data successfully deleted for user {user_id}")
        await message.answer("Ваше участие в розыгрыше отменено. Все данные удалены.", reply_markup=get_main_keyboard())
        await message.answer("Чтобы начать заново, отправьте команду /start")

async def show_registration_number(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await db.db_operation('select', user_id=user_id)
    
    if user_data and user_data[8] is not None:  # Проверяем наличие registration_number (индекс 8)
        registration_number = user_data[8]
        await message.answer(f"Ваш порядковый номер в розыгрыше: {registration_number}")
    else:
        await message.answer("Извините, вы ещё не зарегистрированы на розыгрыш.")

def register_handlers_user_input(dp):
    dp.callback_query.register(process_callback_input)
    dp.message.register(process_input, ~F.contact & ~F.text.in_(["Показать мои данные", "Отменить участие"]))
    dp.message.register(process_phone_contact, F.contact)
    dp.message.register(show_current_data, F.text == "Показать мои данные")
    dp.message.register(cancel_participation, F.text == "Отменить участие")