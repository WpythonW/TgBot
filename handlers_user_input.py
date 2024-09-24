from aiogram import types, F
from aiogram.fsm.context import FSMContext
from database import db_operation
from keyboards import get_inline_keyboard, get_main_keyboard, get_phone_keyboard, get_subscription_keyboard
from aiogram.types import Message, CallbackQuery
import json, logging
from config import CHANNEL_NAME
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def process_callback_input(callback_query: CallbackQuery, state: FSMContext):
    action = callback_query.data
    logging.info(f"Получен callback: {action}")

    user_data = await state.get_data()
    last_bot_message_id = user_data.get('last_bot_message_id')

    # Удаляем предыдущее сообщение с запросом ввода, если оно существует
    if last_bot_message_id:
        try:
            await callback_query.bot.delete_message(callback_query.message.chat.id, last_bot_message_id)
        except Exception as e:
            logging.error(f"Ошибка при удалении предыдущего сообщения: {e}")

    if action.startswith("change_"):
        field = action[7:]
        logging.info(f"Изменяемое поле: {field}")
        if field == "phone":
            await process_phone_share(callback_query.message, state)
        else:
            field_names = {'email': 'почту', 'city': 'город', 'post_link': 'ссылку на пост', 'name': 'имя', 'company': 'название компании', 'position': 'должность'}
            if field in field_names:
                msg = await callback_query.message.answer(f"Пожалуйста, введите {field_names[field]}:")#, reply_markup=get_main_keyboard())

                await state.update_data(last_bot_message_id=msg.message_id, editing_field=field)
                logging.info(f"Запрошено изменение поля: {field}")
            else:
                await callback_query.answer("Неизвестное поле")
                logging.warning(f"Получено неизвестное поле: {field}")
    elif action == "send_data":
        await request_subscription(callback_query, state)
    elif action == "check_subscription":
        await save_data(callback_query, state)
    else:
        await callback_query.answer("Неизвестное действие")
    
    await callback_query.answer()

async def request_subscription(callback_query: CallbackQuery, state: FSMContext):
    keyboard = get_subscription_keyboard()
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

async def save_data(callback_query: CallbackQuery, state: FSMContext):
    try:
        user_data = await state.get_data()
        user_id = callback_query.from_user.id
        db_data = {field: user_data.get(field) for field in ['name', 'email', 'city', 'post_link', 'phone', 'company', 'position']}
        await db_operation('update', user_id=user_id, **db_data)
        
        # Получаем или создаем порядковый номер
        registration_number = await db_operation('get_or_create_registration_number', user_id=user_id)
        
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
        await message.delete()
        
        last_bot_message_id = user_data.get('last_bot_message_id')
        if last_bot_message_id:
            try:
                await message.bot.delete_message(message.chat.id, last_bot_message_id)
            except:
                pass
        
        if editing_field == "phone":
            phone_request_message_id = user_data.get('phone_request_message_id')
            if phone_request_message_id:
                try:
                    await message.bot.delete_message(message.chat.id, phone_request_message_id)
                except:
                    pass
        
        await update_user_data(message, state)
        await state.update_data(editing_field=None, last_bot_message_id=None, phone_request_message_id=None)

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

    # Показываем main_keyboard без дополнительного текста
    #await message.answer(text="", reply_markup=get_main_keyboard())
    # Обновляем клавиатуру последнего сообщения
    #await message.bot.edit_message_reply_markup(
    #    chat_id=message.chat.id,
    #    message_id=message.message_id,
    #    #reply_markup=get_main_keyboard()
    #)

async def send_data(callback_query: CallbackQuery, state: FSMContext):
    keyboard = get_subscription_keyboard()
    await callback_query.message.edit_reply_markup(reply_markup=keyboard)

def register_handlers_user_input(dp):
    dp.callback_query.register(process_callback_input)
    dp.message.register(process_input, ~F.contact & ~F.text.in_(["Показать мои данные", "Отменить участие"]))
    dp.message.register(process_phone_contact, F.contact)
    dp.message.register(show_current_data, F.text == "Показать мои данные")
    dp.message.register(cancel_participation, F.text == "Отменить участие")

async def show_current_data(message: Message, state: FSMContext):
    new_message = await message.answer("Загрузка данных...", reply_markup=get_main_keyboard())

    await state.update_data(data_message_id=new_message.message_id)
    await update_user_data(message, state)

async def process_phone_share(message: Message, state: FSMContext):
    keyboard = get_phone_keyboard()
    msg = await message.answer("Нажмите кнопку, чтобы поделиться номером телефона:", reply_markup=keyboard)
    await state.update_data(editing_field="phone", phone_request_message_id=msg.message_id)

async def process_phone_contact(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone, editing_field=None)
    
    await message.delete()
    
    user_data = await state.get_data()
    phone_request_message_id = user_data.get('phone_request_message_id')
    if phone_request_message_id:
        try:
            await message.bot.delete_message(message.chat.id, phone_request_message_id)
        except:
            pass
    
    await update_user_data(message, state)

async def cancel_participation(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await db_operation('update', user_id=user_id, email=None, city=None, post_link=None, phone=None, name=None, company=None, position=None)
    await state.clear()
    await message.answer("Ваше участие в розыгрыше отменено. Все данные удалены.", reply_markup=get_main_keyboard())
    await message.answer("Чтобы начать заново, отправьте команду /start")

def register_handlers_user_input(dp):
    dp.callback_query.register(process_callback_input)
    dp.message.register(process_input, ~F.contact & ~F.text.in_(["Показать мои данные", "Отменить участие"]))
    dp.message.register(process_phone_contact, F.contact)
    dp.message.register(show_current_data, F.text == "Показать мои данные")
    dp.message.register(cancel_participation, F.text == "Отменить участие")