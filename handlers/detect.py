import asyncio
import logging
import re

from aiogram import Bot, Router, F
from aiogram.types import Message

from keyboards.build_category_keyboard import build_category_keyboard
from storage import in_memory
from utils.tools import generate_uuid

router = Router()

phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')

@router.message(F.text)
async def detect_recommendation(message: Message, bot: Bot):
    if message.chat.type == "private":
        # Пропускаем личные чаты
        return

    message_text = message.text.lower()
    if list(filter(lambda x: x.type == 'url', message.entities)) or bool(phone_pattern.search(message_text)):
        logging.info(f"Обнаружена рекомендация: {message_text}")
        uuid = generate_uuid(message.chat.id, message.message_id)
        in_memory.tmp_msg[uuid] = message

        # Кнопки выбора категории
        keyboard = build_category_keyboard(uuid)

        reply_msg = await message.reply(
            "👀 Похоже, это рекомендация. Хотите сохранить? Выберите категорию:",
            reply_markup=keyboard
        )
        await asyncio.sleep(60)  # ждём 60 секунд
        await bot.delete_message(chat_id=reply_msg.chat.id, message_id=reply_msg.message_id)

