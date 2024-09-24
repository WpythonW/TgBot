from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import json
from config import CHANNEL_INVITE_LINK, CHANNEL_NAME

def get_inline_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Изменить имя", callback_data="change_name")],
        [InlineKeyboardButton(text="Изменить название компании", callback_data="change_company")],
        [InlineKeyboardButton(text="Изменить должность", callback_data="change_position")],
        [InlineKeyboardButton(text="Изменить почту", callback_data="change_email")],
        [InlineKeyboardButton(text="Изменить город", callback_data="change_city")],
        [InlineKeyboardButton(text="Изменить ссылку на пост", callback_data="change_post_link")],
        [InlineKeyboardButton(text="Изменить номер телефона", callback_data="change_phone")],
        #[InlineKeyboardButton(text=f"Подписаться на канал {CHANNEL_NAME}", url=CHANNEL_INVITE_LINK)],
        [InlineKeyboardButton(text="Отправить данные", callback_data="send_data")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_subscription_keyboard():
    keyboard = [
        [InlineKeyboardButton(text=f"Подписаться на канал {CHANNEL_NAME}", url=CHANNEL_INVITE_LINK)],
        [InlineKeyboardButton(text="Я подписался", callback_data="check_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Показать мои данные")],
            [KeyboardButton(text="Отменить участие")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_phone_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер телефона", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard