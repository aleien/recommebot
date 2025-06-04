import re

from aiogram import Bot, Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from fsm.states import ManualRecommend
from logic_save import check_recommendation
from logic_save import manual_recommendation
from storage import in_memory
from utils.tools import extract_link

router = Router()


@router.message(StateFilter(None), Command("save"))
async def handle_save_manual(message: Message, bot: Bot, state: FSMContext):
    await manual_recommendation(message.reply_to_message, bot, state)


@router.callback_query(F.data.startswith("cancel"))
async def handle_cancel(callback: CallbackQuery, bot: Bot, state: FSMContext):
    uuid = callback.data.split("|")[1]

    in_memory.tmp_msg.pop(uuid, None)
    in_memory.active_editors.pop(uuid, None)
    msg_id = in_memory.confirmation_msgs.pop(uuid, None)
    await state.clear()

    if msg_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except TelegramBadRequest:
            pass

    await callback.answer("❌ Отменено")


@router.message(StateFilter(None), F.text)
async def detect_recommendation(message: Message, bot: Bot, state: FSMContext):
    if not message.from_user.is_bot:
        await check_recommendation(message, bot, state)
