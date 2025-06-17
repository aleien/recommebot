from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from logic_save import check_recommendation
from storage import in_memory
from utils.logger import log

router = Router()


@router.callback_query(F.data.startswith("cancel|"))
async def handle_cancel(callback: CallbackQuery, bot: Bot, state: FSMContext):
    uuid = callback.data.split("|")[1]

    in_memory.tmp_msg.pop(uuid, None)
    in_memory.active_editors.pop(uuid, None)
    in_memory.confirmation_msgs.pop(uuid, None)
    await state.clear()

    try:
        await callback.bot.delete_message(callback.message.chat.id, callback.message.message_id)
    except TelegramBadRequest:
        pass

    await callback.answer("❌ Отменено")


@router.message(StateFilter(None), F.text)
async def detect_recommendation(message: Message, bot: Bot, state: FSMContext):
    if not message.from_user.is_bot:
        await check_recommendation(message, bot, state)


@router.message(F.text)
async def detect_any(message: Message, bot: Bot, state: FSMContext):
    log.info("Не попало в другие хэндлеры: ")
    log.info(f"Стейт {state}")
    log.info(f"Текст: {message.text}")
    log.info(f"Описание: {message.caption}")
    log.info(f"id: {message.message_id}")