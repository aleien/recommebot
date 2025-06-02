from aiogram import F, Router, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery, )

from fsm.states import ManualRecommend
from logic_save import save, save_manual
from utils.logger import log

router = Router()


@router.callback_query(ManualRecommend.selecting_category, F.data.startswith("save|"))
async def handle_manual_category(callback: CallbackQuery, bot: Bot, state: FSMContext):
    _, category, uuid = callback.data.split("|")
    state = await state.get_state()
    log.info(f"Текущий стейт в хендлере (manual): {state}")
    await save_manual(
        bot=bot,
        category=category,
        uuid=uuid,
        from_user_id=callback.from_user.id,
        answer_func=callback.answer,
        edit_func=callback.message.edit_text)


@router.callback_query(StateFilter(None), F.data.startswith("save|"))
async def handle_save_callback(callback: CallbackQuery, bot: Bot, state: FSMContext):
    _, category, uuid = callback.data.split("|")
    state = await state.get_state()
    log.info(f"Текущий стейт в хендлере: {state}")
    await save(
        bot=bot,
        category=category,
        uuid=uuid,
        from_user_id=callback.from_user.id,
        answer_func=callback.answer,
        edit_func=callback.message.edit_text)



