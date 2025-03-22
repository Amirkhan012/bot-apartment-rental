from aiogram.filters.state import State, StatesGroup


class Form(StatesGroup):
    basic = State()
    photos = State()
    address = State()
    confirm_address = State()
    search_filters = State()
