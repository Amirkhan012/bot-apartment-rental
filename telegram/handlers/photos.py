from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from telegram.states import Form


router = Router()


@router.message(
    StateFilter(Form.photos),
    lambda message: message.content_type == "photo"
)
async def process_photo(message: types.Message, state: FSMContext) -> None:
    """Сохраняет входящие фотографии при загрузке объявления."""
    data = await state.get_data()
    photos = data.get("photo_file_ids", [])

    if message.photo:
        file_id = message.photo[-1].file_id
        photos.append(file_id)
        await state.update_data(photo_file_ids=photos)
        await message.reply(
            f"Фото получено (всего: {len(photos)}). Отправьте ещё или /done.")


@router.message(StateFilter(Form.photos), Command("done"))
async def finish_photos(message: types.Message, state: FSMContext) -> None:
    """Завершает создание объявления после загрузки фотографий."""
    data = await state.get_data()
    photos = data.get("photo_file_ids", [])
    if not photos:
        await message.reply(
            "Вы не загрузили фото. Загрузите хотя бы одно фото.")
        return

    await state.set_state(Form.address)
    await message.reply(
        "Теперь введите адрес квартиры. Например:"
        "\nМосква, Красная площадь, 1")
