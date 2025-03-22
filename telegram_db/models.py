import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Boolean)
from sqlalchemy.orm import declarative_base, relationship


Base = declarative_base()


class Apartment(Base):
    __tablename__ = 'apartments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = Column(String, nullable=False)
    city = Column(String, nullable=False)
    street = Column(String, nullable=True)
    address = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    storey = Column(Integer, nullable=True, default=0)
    rooms = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_available = Column(Boolean, default=True, nullable=False)

    photos = relationship(
        "Photo",
        back_populates="apartment",
        cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = 'photos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=False)
    file_id = Column(String, nullable=False)

    apartment = relationship("Apartment", back_populates="photos")
