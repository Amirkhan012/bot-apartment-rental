from typing import Tuple

from aiogram import Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from telegram.states import Form


router = Router()


def validate_basic_data(text: str) -> Tuple[float, str, int]:
    """
    Парсит строку с базовыми данными в формате:
      "Цена, этаж, количество комнат, описание."
    и возвращает кортеж (price, description, rooms).
    Выбрасывает ValueError, если формат неверный.
    """
    parts = [x.strip() for x in text.split(',', 3)]
    if len(parts) != 4:
        raise ValueError(
            "Ожидается 4 параметра: Цена, этаж, количество комнат, описание.")
    try:
        price = float(parts[0])
    except ValueError:
        raise ValueError("Цена должна быть числом.")
    try:
        storey = float(parts[1])
    except ValueError:
        raise ValueError("Цена должна быть числом.")
    try:
        rooms = int(parts[2])
    except ValueError:
        raise ValueError("Количество комнат должно быть целым числом.")
    description = parts[3]
    return price, storey, rooms, description,


@router.message(StateFilter(Form.basic))
async def process_basic_info(
    message: types.Message,
    state: FSMContext
) -> None:
    """Обрабатывает базовые данные и переходит к загрузке фото."""
    try:
        price, storey, rooms, description = validate_basic_data(message.text)
    except ValueError as e:
        await message.reply(f"Ошибка: {e}")
        return

    await state.update_data(
        price=price,
        storey=storey,
        rooms=rooms,
        description=description,
        owner_id=str(message.from_user.id),
        photo_file_ids=[]
    )
    await state.set_state(Form.photos)
    await message.reply(
        "Теперь отправьте минимум одно фото. "
        "После завершения введите - /done.")
