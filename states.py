from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    waiting_for_email = State()
    waiting_for_city = State()
    waiting_for_post_link = State()
    waiting_for_phone = State()