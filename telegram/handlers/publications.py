from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from telegram_db.crud import (
    get_apartments_by_owner, delete_apartment, update_apartment_availability)
from telegram_db.db import AsyncSessionLocal


router = Router()

PAGE_SIZE = 5


@router.message(F.text == "📃 Мои публикации")
async def my_publications(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик кнопки "📃 Мои публикации".
    Извлекает публикации для текущего пользователя из базы данных
    и выводит их красиво, с информацией и группами фотографий по 5 штук.
    """
    owner_id = str(message.from_user.id)

    apartments = await get_apartments_by_owner(owner_id)

    if not apartments:
        await message.answer("📃 У вас нет публикаций.")
        return

    data = await state.get_data()
    current_page = data.get("current_publications_page", 0)
    total_pages = (len(apartments) - 1) // PAGE_SIZE + 1

    start_index = current_page * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    pubs_page = apartments[start_index:end_index]

    for apt in pubs_page:
        response = (
            f"📢 Объявление ID: {apt.id}\n"
            f"🏠 Город: {apt.city}\n"
            f"🛏️ Улица: {apt.street}\n"
            f"🏠 Адрес: {apt.address}\n"
            f"🏢 Этаж: {apt.storey}\n"
            f"🛏️ Комнат: {apt.rooms}\n"
            f"💰 Цена: {apt.price} руб.\n"
            f"📅 Статус: {'✅ Доступно' if apt.is_available else '❌ Занято'}\n"
            f"📝 Описание: {apt.description}\n"
        )

        if apt.photos:
            photo_ids = [photo.file_id for photo in apt.photos]
            chunks = [photo_ids[i:i+5] for i in range(0, len(photo_ids), 5)]
            for chunk in chunks:
                media = [
                    types.InputMediaPhoto(media=file_id) for file_id in chunk]
                await message.bot.send_media_group(
                    chat_id=message.chat.id, media=media)

        action_kb = InlineKeyboardBuilder()
        action_kb.button(
            text="❌ Удалить",
            callback_data=f"delete|{apt.id}")
        action_kb.button(
            text="🔄 Изменить статус",
            callback_data=f"toggle|{apt.id}")
        action_kb.adjust(2)
        await message.answer(
            response,
            reply_markup=action_kb.as_markup())

    nav_kb = InlineKeyboardBuilder()
    if current_page > 0:
        nav_kb.button(text="⬅️ Назад", callback_data="pubs_prev")
    if current_page < total_pages - 1:
        nav_kb.button(text="➡️ Далее", callback_data="pubs_next")
    nav_kb.adjust(1)
    if nav_kb.buttons:
        await message.answer(
            f"Страница {current_page+1} из {total_pages}",
            reply_markup=nav_kb.as_markup())

    await state.update_data(current_publications_page=current_page)


@router.callback_query(F.data.startswith("pubs_"))
async def publications_pagination(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    Обрабатывает навигацию по страницам публикаций.
    Кнопки "⬅️ Назад" и "➡️ Далее" изменяют номер текущей страницы.
    """
    data = callback.data
    user_data = await state.get_data()
    current_page = user_data.get("current_publications_page", 0)

    owner_id = str(callback.from_user.id)
    async with AsyncSessionLocal() as session:
        apartments = await get_apartments_by_owner(session, owner_id)
    total_pages = (len(apartments) - 1) // PAGE_SIZE + 1

    if data == "pubs_next" and current_page < total_pages - 1:
        current_page += 1
    elif data == "pubs_prev" and current_page > 0:
        current_page -= 1

    await state.update_data(current_publications_page=current_page)

    await my_publications(callback.message, state)
    await callback.answer()


@router.callback_query(F.data.startswith("delete|"))
async def delete_publication(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    Обрабатывает кнопку "Удалить" для публикации.
    Извлекает id объявления из callback_data и удаляет его из базы,
    если публикация принадлежит текущему пользователю.
    """
    _, apt_id_str = callback.data.split("|")
    apt_id = int(apt_id_str)
    owner_id = str(callback.from_user.id)

    async with AsyncSessionLocal() as session:
        try:
            await delete_apartment(session, apt_id, owner_id)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return
    await callback.message.answer(f"Объявление {apt_id} удалено.")
    await callback.answer()

    await my_publications(callback.message, state)


@router.callback_query(F.data.startswith("toggle|"))
async def toggle_availability(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    Обрабатывает кнопку "Изменить статус" для публикации.
    Извлекает id объявления и переключает его доступность.
    """
    _, apt_id_str = callback.data.split("|")
    apt_id = int(apt_id_str)
    owner_id = str(callback.from_user.id)

    async with AsyncSessionLocal() as session:
        try:
            apt = await update_apartment_availability(
                session, apt_id, owner_id)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return
    new_status = "✅ Доступно" if apt.is_available else "❌ Занято"
    await callback.message.answer(
        f"Статус объявления {apt_id} изменен на {new_status}.")
    await callback.answer()
