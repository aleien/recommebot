from aiogram.types import (
    InlineKeyboardMarkup
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import CATEGORIES


def build_category_keyboard(uuid: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for category in CATEGORIES:
        builder.button(
            text=category,
            callback_data=f"save|{category}|{uuid}"
        )
    builder.button(
        text="Отмена",
        callback_data=f"cancel|{uuid}"
    )

    builder.adjust(2)  # по 2 кнопки в ряд
    return builder.as_markup()


def build_is_recommendation_keyboard(uuid: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Да", callback_data="is_recommendatin")
    builder.button(text="Нет", callback_data=f"cancel|{uuid}")
    builder.adjust(2)  # по 2 кнопки в ряд
    return builder.as_markup()
