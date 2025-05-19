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

    builder.adjust(2)  # по 2 кнопки в ряд
    return builder.as_markup()
