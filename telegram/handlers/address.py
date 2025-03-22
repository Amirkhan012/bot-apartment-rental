from aiogram import Router, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from telegram_db.crud import create_apartment
from telegram.states import Form
from telegram.geocoding import geocode_address


router = Router()


@router.message(StateFilter(Form.address))
async def process_address(message: types.Message, state: FSMContext) -> None:
    """
    Получает адрес и выводит пользователю удобные варианты или
    возможность отправить на модерацию.
    """
    address = message.text
    addresses = await geocode_address(address)

    if not addresses:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔄 Попробовать снова", callback_data="addr_retry")
        builder.button(
            text="✅ Отправить адрес на модерацию",
            callback_data="addr_mod_custom")
        builder.adjust(1)

        await state.update_data(custom_address=address)

        await message.reply(
            "❌ Не удалось найти точный адрес.\n\n"
            "Вы можете уточнить адрес и попробовать снова, или "
            "отправить введённый вами адрес модератору.",
            reply_markup=builder.as_markup()
        )
        return

    await state.update_data(all_addresses=addresses, current_index=0)
    await show_address_options(message, state)


async def show_address_options(
    message: types.Message,
    state: FSMContext
) -> None:
    """
    Отображает пользователю до 5 адресов в понятном виде.
    """
    user_data = await state.get_data()
    addresses = user_data["all_addresses"]
    current_index = user_data["current_index"]

    builder = InlineKeyboardBuilder()
    response_text = "🏠 Найденные адреса:\n\n"

    next_addresses = addresses[current_index:current_index+5]

    for idx, addr in enumerate(next_addresses, start=1+current_index):
        response_text += (
            f"Вариант {idx}:\n"
            f"📌 Номер дома: {addr['house_number']}\n"
            f"📍 Улица: {addr['road']}\n"
            f"📍 Район: {addr['region']}\n"
            f"🌆 Город: {addr['city']}\n\n"
        )
        builder.button(text=f"Вариант {idx}", callback_data=f"addr|{idx-1}")

    if len(addresses) > current_index + 5:
        builder.button(text="➡️ Ещё варианты", callback_data="addr_more")

    builder.button(text="🔄 Попробовать снова", callback_data="addr_retry")
    builder.button(text="⚠️ Отправить модератору", callback_data="addr_mod")
    builder.adjust(1, repeat=True)

    await message.reply(response_text, reply_markup=builder.as_markup())
    await state.set_state(Form.confirm_address)


@router.callback_query(StateFilter(Form.confirm_address))
async def confirm_address(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """
    Обработчик нажатий на кнопки выбора адреса и дополнительных действий.
    """
    data = callback.data
    current_state = await state.get_state()
    user_data = await state.get_data()

    if data == "addr_retry":
        if current_state not in [
            Form.confirm_address.state,
            Form.address.state
        ]:
            await callback.answer(
                "⚠️ Действие уже недоступно.",
                show_alert=True)
            return
        await callback.message.answer("🏠 Пожалуйста, введите адрес ещё раз:")
        await state.set_state(Form.address)
        await callback.answer()
        return

    if data in ["addr_mod_custom", "addr_mod"]:
        custom_address = user_data.get("custom_address")
        if current_state != Form.confirm_address.state or not custom_address:
            await callback.answer(
                "⚠️ Нет адреса для отправки модератору.",
                show_alert=True)
            return
        await callback.message.answer(
            f"✅ Ваш адрес:\n\n{custom_address}\n\n"
            "отправлен на модерацию. Мы свяжемся с вами после проверки."
        )
        await state.clear()
        await callback.answer()
        return

    if data == "addr_more":
        all_addresses = user_data.get("all_addresses")
        current_index = user_data.get("current_index", 0)

        if current_state != Form.confirm_address.state or not all_addresses:
            await callback.answer(
                "⚠️ Варианты уже не доступны.",
                show_alert=True)
            return

        if current_index + 5 >= len(all_addresses):
            await callback.answer("⚠️ Больше вариантов нет.", show_alert=True)
            return

        user_data["current_index"] += 5
        await state.update_data(current_index=user_data["current_index"])
        await show_address_options(callback.message, state)
        await callback.answer()
        return

    if "|" in data:
        if current_state != Form.confirm_address.state:
            await callback.answer(
                "⚠️ Действие уже не актуально.",
                show_alert=True)
            return

        _, index = data.split("|")
        all_addresses = user_data.get("all_addresses", [])

        try:
            chosen_address = all_addresses[int(index)]
        except (IndexError, ValueError):
            await callback.answer(
                "⚠️ Ошибка выбора варианта. Попробуйте снова.",
                show_alert=True)
            return

        city = chosen_address["city"]
        street = chosen_address["road"]
        full_address = (
            f"{chosen_address['road']}, {chosen_address['house_number']}, "
            f"{chosen_address['region']}, {city}"
        )

        await state.update_data(address=full_address, city=city, street=street)

        await create_apartment(
                owner_id=user_data["owner_id"],
                city=city,
                street=street,
                address=full_address,
                price=user_data["price"],
                storey=user_data["storey"],
                rooms=user_data["rooms"],
                description=user_data["description"],
                photo_file_ids=user_data["photo_file_ids"]
            )

        await callback.message.answer(
            f"✅ Вы выбрали адрес:\n\n"
            f"Город: {city}\nАдрес: {full_address}"
            "\n\n🎉 Объявление успешно создано!"
        )
        await state.clear()
        await callback.answer()
