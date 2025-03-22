from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from telegram_db.db import AsyncSessionLocal
from telegram_db.models import Apartment
from telegram.states import Form

router = Router()
PAGE_SIZE = 5


@router.message(Command("search_rentals"))
async def start_custom_search(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Инициализирует фильтры и переводит пользователя в состояние поиска аренды.
    """
    initial_filters = {
        "город": "",
        "адрес": "",
        "цена мин": "",
        "цена макс": "",
        "комнаты": "",
        "этаж": ""
    }
    await state.update_data(
        search_filters=initial_filters,
        current_rentals_page=0,
        current_edit_field=None
    )
    await state.set_state(Form.search_filters)
    await show_filters_form(message, state)


async def show_filters_form(message: types.Message, state: FSMContext) -> None:
    """
    Отправляет новое сообщение с текущими фильтрами через inline‑клавиатуру.
    """
    data = await state.get_data()
    filters = data.get("search_filters", {})

    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Город: {filters.get('город') or 'Не указано'}",
        callback_data="edit_город")
    builder.button(
        text=f"Адрес: {filters.get('адрес') or 'Не указано'}",
        callback_data="edit_адрес")
    builder.button(
        text=f"Цена мин: {filters.get('цена мин') or 'Не указано'}",
        callback_data="edit_цена мин")
    builder.button(
        text=f"Цена макс: {filters.get('цена макс') or 'Не указано'}",
        callback_data="edit_цена макс")
    builder.button(
        text=f"Комнаты: {filters.get('комнаты') or 'Не указано'}",
        callback_data="edit_комнаты")
    builder.button(
        text=f"Этаж: {filters.get('этаж') or 'Не указано'}",
        callback_data="edit_этаж")
    builder.adjust(1)

    builder.button(text="🔄 Сбросить фильтры", callback_data="reset_filters")
    builder.button(text="✅ Применить фильтры", callback_data="apply_filters")

    await message.answer(
        "Заполните фильтры поиска (нажмите, чтобы изменить):",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith("edit_"))
async def edit_filter_callback(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    При нажатии на кнопку редактирования сохраняется название поля для
    изменения, и бот запрашивает новое значение.
    """
    field = callback.data.replace("edit_", "")
    await state.update_data(current_edit_field=field)
    await callback.message.answer(f"Введите новое значение для '{field}':")
    await callback.answer()


@router.callback_query(F.data == "reset_filters")
async def reset_filters_callback(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    Сбрасывает фильтры в исходное состояние.
    """
    initial_filters = {
        "город": "",
        "адрес": "",
        "цена мин": "",
        "цена макс": "",
        "комнаты": "",
        "этаж": ""
    }
    await state.update_data(
        search_filters=initial_filters,
        current_edit_field=None,
        current_rentals_page=0
    )
    await callback.message.answer("Фильтры сброшены.")
    await show_filters_form(callback.message, state)
    await callback.answer("Фильтры сброшены.")


@router.message()
async def process_field_value(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Обрабатывает текстовые сообщения.
    Если в FSM установлено поле для редактирования, считается, что
    это новое значение для него.
    """
    data = await state.get_data()
    current_field = data.get("current_edit_field")
    if not current_field:
        return

    search_filters = data.get("search_filters", {})
    if current_field in ["цена мин", "цена макс"]:
        try:
            float(message.text)
        except ValueError:
            await message.answer(
                "Введите корректное числовое значение для цены.")
            return
    elif current_field in ["комнаты", "этаж"]:
        try:
            int(message.text)
        except ValueError:
            await message.answer("Введите целое число для данного поля.")
            return

    search_filters[current_field] = message.text
    await state.update_data(
        search_filters=search_filters, current_edit_field=None)
    await message.answer(f"Значение для '{current_field}' обновлено.")
    await show_filters_form(message, state)


@router.callback_query(F.data == "apply_filters")
async def apply_filters_callback(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    При нажатии кнопки «Применить фильтры» выполняется запрос в БД с учетом
    указанных фильтров и выводятся результаты.
    """
    data = await state.get_data()
    filters = data.get("search_filters", {})
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Apartment)
            .options(selectinload(Apartment.photos))
            .where(Apartment.is_available)
        )
        if filters.get("город"):
            stmt = stmt.where(Apartment.city.ilike(f"%{filters['город']}%"))
        if filters.get("адрес"):
            stmt = stmt.where(Apartment.address.ilike(f"%{filters['адрес']}%"))
        if filters.get("цена мин"):
            try:
                price_min = float(filters["цена мин"])
                stmt = stmt.where(Apartment.price >= price_min)
            except ValueError:
                pass
        if filters.get("цена макс"):
            try:
                price_max = float(filters["цена макс"])
                stmt = stmt.where(Apartment.price <= price_max)
            except ValueError:
                pass
        if filters.get("комнаты"):
            try:
                rooms = int(filters["комнаты"])
                stmt = stmt.where(Apartment.rooms == rooms)
            except ValueError:
                pass
        if filters.get("этаж"):
            try:
                storey = int(filters["этаж"])
                stmt = stmt.where(Apartment.storey == storey)
            except ValueError:
                pass
        result = await session.execute(stmt)
        apartments = result.scalars().all()

    if not apartments:
        await callback.message.answer(
            "❌ По заданным фильтрам ничего не найдено.")
        await callback.answer()
        return

    await state.update_data(current_rentals_page=0)
    await display_custom_rentals(callback.message, state, apartments)
    await callback.answer("Фильтры применены!")


async def display_custom_rentals(
    message: types.Message,
    state: FSMContext,
    apartments: list
) -> None:
    """
    Отображает найденные объявления с пагинацией (PAGE_SIZE на страницу).
    """
    data = await state.get_data()
    current_page = data.get("current_rentals_page", 0)
    total_pages = (len(apartments) - 1) // PAGE_SIZE + 1
    start_index = current_page * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    rentals_page = apartments[start_index:end_index]

    for apt in rentals_page:
        if apt.photos:
            photo_ids = [photo.file_id for photo in apt.photos]
            chunks = [photo_ids[i:i+5] for i in range(0, len(photo_ids), 5)]
            for chunk in chunks:
                media = [
                    types.InputMediaPhoto(media=file_id) for file_id in chunk]
                await message.bot.send_media_group(
                    chat_id=message.chat.id, media=media)
        response = (
            f"📢 <b>Объявление ID:</b> {apt.id}\n"
            f"🏠 <b>Город:</b> {apt.city}\n"
            f"🛏️ <b>Улица:</b> {apt.street}\n"
            f"🏠 <b>Адрес:</b> {apt.address}\n"
            f"🏢 <b>Этаж:</b> {apt.storey}\n"
            f"🛏️ <b>Комнат:</b> {apt.rooms}\n"
            f"💰 <b>Цена:</b> {apt.price} руб.\n"
            f"📝 <b>Описание:</b> {apt.description}\n"
            f"👤 <b>Владелец:</b> <a href='tg://user?id={apt.owner_id}'>Контакт</a>\n"
        )
        await message.answer(response, parse_mode="HTML")

    builder = InlineKeyboardBuilder()
    if current_page > 0:
        builder.button(text="⬅️ Назад", callback_data="custom_prev")
    if current_page < total_pages - 1:
        builder.button(text="➡️ Далее", callback_data="custom_next")
    builder.adjust(1)
    if builder.buttons:
        await message.answer(
            f"Страница {current_page+1} из {total_pages}",
            reply_markup=builder.as_markup())
    await state.update_data(current_rentals_page=current_page)


@router.callback_query(F.data.startswith("custom_"))
async def custom_rentals_pagination(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    Обрабатывает кнопки навигации по страницам (custom_prev и custom_next),
    обновляя номер текущей страницы и выводя объявления.
    """
    data_cb = callback.data
    user_data = await state.get_data()
    current_page = user_data.get("current_rentals_page", 0)
    filters = user_data.get("search_filters", {})

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Apartment)
            .options(selectinload(Apartment.photos))
            .where(Apartment.is_available)
        )
        if filters.get("город"):
            stmt = stmt.where(Apartment.city.ilike(f"%{filters['город']}%"))
        if filters.get("адрес"):
            stmt = stmt.where(Apartment.address.ilike(f"%{filters['адрес']}%"))
        if filters.get("цена мин"):
            try:
                price_min = float(filters["цена мин"])
                stmt = stmt.where(Apartment.price >= price_min)
            except ValueError:
                pass
        if filters.get("цена макс"):
            try:
                price_max = float(filters["цена макс"])
                stmt = stmt.where(Apartment.price <= price_max)
            except ValueError:
                pass
        if filters.get("комнаты"):
            try:
                rooms = int(filters["комнаты"])
                stmt = stmt.where(Apartment.rooms == rooms)
            except ValueError:
                pass
        if filters.get("этаж"):
            try:
                storey = int(filters["этаж"])
                stmt = stmt.where(Apartment.storey == storey)
            except ValueError:
                pass
        result = await session.execute(stmt)
        apartments = result.scalars().all()

    total_pages = (len(apartments) - 1) // PAGE_SIZE + 1
    if data_cb == "custom_next" and current_page < total_pages - 1:
        current_page += 1
    elif data_cb == "custom_prev" and current_page > 0:
        current_page -= 1

    await state.update_data(current_rentals_page=current_page)
    await display_custom_rentals(callback.message, state, apartments)
    await callback.answer()
