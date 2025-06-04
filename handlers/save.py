from aiogram import F, Router, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery, Message, )

from fsm.states import ManualRecommend
from keyboards.build_category_keyboard import build_category_keyboard
from logic_save import save, save_manual
from storage import in_memory
from utils.logger import log

router = Router()


@router.callback_query(ManualRecommend.selecting_category, F.data.startswith("save|"))
async def handle_manual_category(callback: CallbackQuery, bot: Bot, state: FSMContext):
    _, category, uuid = callback.data.split("|")
    current_state = await state.get_state()
    log.info(f"Текущий стейт в хендлере (manual): {current_state}")
    await save_manual(
        bot=bot,
        category=category,
        uuid=uuid,
        from_user_id=callback.from_user.id,
        answer_func=callback.answer,
        edit_func=callback.message.edit_text,
        state=state)


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
        edit_func=callback.message.edit_text,
        state=state)


@router.callback_query(F.data.startswith("confirm|"))
async def confirm_callback(callback: CallbackQuery):
    uuid = callback.data.split("|")[1]
    user_id = callback.from_user.id

    # Защита от параллельного редактирования
    if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != user_id:
        await callback.answer("⚠️ Уже обрабатывается другим участником.", show_alert=True)
        return

    in_memory.active_editors[uuid] = user_id

    # Показать категории
    keyboard = build_category_keyboard(uuid)
    log.info(f"Показываем категории для сохранения сообщения uuid={uuid}")
    await callback.message.reply_to_message.reply(
        "📂 Выберите категорию:",
        reply_markup=keyboard
    )

    # Удалить сообщение подтверждения
    msg_id = in_memory.confirmation_msgs.pop(uuid, None)
    if msg_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, msg_id)
        except TelegramBadRequest:
            pass


    await callback.answer()


@router.message(F.text)
async def last_call(message: Message, state: FSMContext):

    current_state = await state.get_state()
    log.info(f"Не попало в другие обработчики, текущий стейт: {current_state}")
    log.info(f"Текущий словарь сообщений {in_memory.tmp_msg}")
    log.info(f"Текущий словарь редакторов {in_memory.active_editors}")

