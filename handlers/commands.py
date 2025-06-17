from aiogram import Bot, Router
from aiogram.filters import Command, StateFilter, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from logic_save import manual_recommendation

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Привет! Я бот, который помогает сохранять рекомендации 🙌")


@router.message(StateFilter(None), Command("save"))
async def handle_save_manual(message: Message, bot: Bot, state: FSMContext):
    await manual_recommendation(message.reply_to_message, bot, state)
