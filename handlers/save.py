from aiogram import F, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
)

from fsm.states import ManualRecommend
from logic_save import save

router = Router()


@router.callback_query(F.data.startswith("save|"))
async def handle_save_callback(callback: CallbackQuery, bot: Bot):
    _, category, uuid = callback.data.split("|")
    await save(
        bot=bot,
        category=category,
        uuid=uuid,
        from_user_id=callback.from_user.id,
        answer_func=callback.answer,
        edit_func=callback.message.edit_text)


@router.message(StateFilter(ManualRecommend.selecting_category), F.data.startswith("save|"))
async def handle_manual_category(callback: CallbackQuery, bot: Bot, state: FSMContext):
    _, category, uuid = callback.data.split("|")
    await save(
        bot=bot,
        category=category,
        uuid=uuid,
        from_user_id=callback.from_user.id,
        answer_func=callback.answer,
        edit_func=callback.message.edit_text)
