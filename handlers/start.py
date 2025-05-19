from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я бот, который помогает сохранять рекомендации 🙌")
