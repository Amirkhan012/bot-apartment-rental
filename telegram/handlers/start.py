from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext

from telegram.handlers import publications, rentals_search_custom
from telegram.states import Form

router = Router()


start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📌 Аренда"),
         KeyboardButton(text="🏠 Арендодатель")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


rent_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


landlord_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить"),
         KeyboardButton(text="📃 Мои публикации")],
        [KeyboardButton(text="Назад")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)


@router.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    """
    Обработчик команды /start.
    Показывает главное меню с выбором между аренда и арендодатель.
    """
    await message.answer(
        "👋 Добро пожаловать! Выберите действие:", reply_markup=start_kb)


@router.message(F.text == "📌 Аренда")
async def rent_placeholder(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Обработчик кнопки '📌 Аренда'.
    Пока выводит заглушку, что раздел аренды скоро заработает,
    и выводит клавиатуру с кнопкой "Назад".
    """
    await rentals_search_custom.start_custom_search(message, state)


@router.message(F.text == "🏠 Арендодатель")
async def landlord_menu(message: types.Message) -> None:
    """
    Обработчик кнопки '🏠 Арендодатель'.
    Показывает меню для арендодателя с кнопками '➕ Добавить',
    '📃 Мои публикации' и кнопкой "Назад".
    """
    await message.answer("Выберите действие:", reply_markup=landlord_kb)


async def cmd_add(message: types.Message, state: FSMContext) -> None:
    """
    Запускает создание объявления и запрашивает базовые данные.
    """
    await state.set_state(Form.basic)
    await message.reply(
        "Введите данные: Цена, этаж, количество комнат, описание\n"
        "Пример: 50000, 1, 2, Уютная квартира|77,2м²  ,"
    )


@router.message(Command("add"))
async def add_publication_command(
    message: types.Message,
    state: FSMContext
) -> None:
    await cmd_add(message, state)


@router.message(F.text == "➕ Добавить")
async def add_publication_button(
    message: types.Message,
    state: FSMContext
) -> None:
    await cmd_add(message, state)


@router.message(F.text == "📃 Мои публикации")
async def my_publications_handler(message: types.Message, state) -> None:
    """
    Обработчик кнопки '📃 Мои публикации'.
    Передаёт управление в модуль publications.
    """
    await publications.my_publications(message, state)


@router.message(F.text == "Назад")
async def go_back(message: types.Message) -> None:
    """
    Обработчик кнопки 'Назад'.
    Возвращает пользователя в главное меню.
    """
    await message.answer("Главное меню:", reply_markup=start_kb)
