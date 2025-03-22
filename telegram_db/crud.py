from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from telegram_db.models import Apartment, Photo
from telegram_db.db import AsyncSessionLocal


async def create_apartment(
    owner_id: str,
    city: str,
    street: str,
    address: str,
    price: float,
    storey: int,
    rooms: int,
    description: str,
    photo_file_ids: list = None,
    is_available: bool = True
) -> Apartment:
    """
    Создает новое объявление о квартире и, если передан список фотографий,
    сразу добавляет их к объявлению.

    Параметры:
      owner_id (str): Telegram ID пользователя, который публикует объявление.
      city (str): Город, где находится квартира.
      street: (str): Улица, где находится квартираю.
      address (str): Полный адрес квартиры.
      price (float): Цена аренды.
      storey (int): Этаж квартиры.
      rooms (int): Количество комнат.
      description (str): Описание квартиры.
      photo_file_ids (list): Список идентификаторов файлов фотографий.
      is_available (bool): Статус доступности.

    Возвращает:
      Apartment: Объект объявления, сохраненный в базе данных.
    """
    if photo_file_ids and len(photo_file_ids) > 50:
        raise ValueError("Можно загрузить максимум 50 фотографий.")

    async with AsyncSessionLocal() as session:
        new_apartment = Apartment(
            owner_id=owner_id,
            city=city,
            street=street,
            address=address,
            price=price,
            storey=storey,
            rooms=rooms,
            description=description,
            is_available=is_available
        )

        if photo_file_ids:
            for file_id in photo_file_ids:
                photo = Photo(file_id=file_id)
                new_apartment.photos.append(photo)

        session.add(new_apartment)
        await session.commit()
        await session.refresh(new_apartment)
        return new_apartment


async def get_apartments_by_owner(owner_id: str) -> list[Apartment]:
    """
    Возвращает список объявлений для указанного владельца.

    Параметры:
      owner_id (str): Telegram ID пользователя, который публиковал объявления.

    Возвращает:
      List[Apartment]: Список объектов Apartment, опубликованных данным
        пользователем.
    """
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Apartment)
            .where(Apartment.owner_id == owner_id)
            .options(selectinload(Apartment.photos))
        )
        result = await session.execute(stmt)
        apartments = result.scalars().all()
        return apartments


async def delete_apartment(
    session: AsyncSession,
    apartment_id: int,
    owner_id: str
) -> None:
    """
    Удаляет объявление по его идентификатору, если оно принадлежит
    указанному владельцу.

    Параметры:
      session (AsyncSession): асинхронная сессия SQLAlchemy.
      apartment_id (int): идентификатор объявления.
      owner_id (str): Telegram ID пользователя, который пытается
        удалить объявление.

    Возвращает:
      None. Если объявление не найдено или не принадлежит владельцу,
      выбрасывает ValueError.
    """
    result = await session.execute(
        select(Apartment).where(Apartment.id == apartment_id))
    apartment = result.scalar_one_or_none()
    if apartment is None:
        raise ValueError(f"Объявление с id {apartment_id} не найдено.")
    if apartment.owner_id != owner_id:
        raise ValueError("Нельзя удалить чужое объявление.")

    await session.delete(apartment)
    await session.commit()


async def update_apartment_availability(
    session: AsyncSession, apartment_id: int, owner_id: str,
) -> Apartment:
    """
    Обновляет поле is_available для объявления
    по его идентификатору, если оно принадлежит указанному владельцу.

    Параметры:
      session (AsyncSession): асинхронная сессия SQLAlchemy.
      apartment_id (int): идентификатор объявления.
      owner_id (str): Telegram ID пользователя, который пытается
        обновить объявление.
      is_available (bool): новое значение для поля доступности.

    Возвращает:
      Обновленный объект Apartment. Если объявление не найдено или не
      принадлежит владельцу, выбрасывает ValueError.
    """
    result = await session.execute(
        select(Apartment).where(Apartment.id == apartment_id))
    apartment = result.scalar_one_or_none()
    if apartment is None:
        raise ValueError(f"Объявление с id {apartment_id} не найдено.")
    if apartment.owner_id != owner_id:
        raise ValueError("Нельзя изменить доступность чужого объявления.")

    apartment.is_available = not apartment.is_available

    await session.commit()
    await session.refresh(apartment)
    return apartment
