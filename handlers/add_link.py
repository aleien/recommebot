from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext

from fsm.states import RecommendState
from utils.logger import log
import re

from aiogram import F
from aiogram import Router
from aiogram.types import (
    Message,
    CallbackQuery,
)

from storage import in_memory
from utils.tools import extract_phone

link_pattern = re.compile(r'https?://\S+')
phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')
router = Router()


@router.callback_query(F.data.startswith("addlink|"))
async def handle_add_link(callback: CallbackQuery, state: FSMContext):
    _, uuid = callback.data.split("|")
    in_memory.pending_links[callback.from_user.id] = uuid
    await state.set_state(RecommendState.typing_link)
    await callback.message.edit_text("✍️ Напишите сообщение с ссылкой или телефоном в ответ на это сообщение.")


@router.message(StateFilter(RecommendState.typing_link), F.text & F.chat.type != "private")
async def handle_link_submission(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in in_memory.pending_links:
        return

    link = message.text.strip()
    if not (link_pattern.search(link) or extract_phone(message)):
        await message.reply("⚠️ Это не похоже на ссылку или номер. Попробуйте ещё раз.")
        return

    uuid = in_memory.pending_links.pop(user_id)
    # Можно сохранить ссылку в tmp_msg[uuid] или сразу отправить в хранилище
    log.info(f"Добавлена ссылка для UUID {uuid}: {link}")
    # Удаляем блокировку
    in_memory.active_editors.pop(uuid, None)
    await state.clear()
    await message.reply("✅ Ссылка добавлена и рекомендация сохранена. Спасибо! 💛")


@router.callback_query(F.data.startswith("cancel|"))
async def handle_cancel(callback: CallbackQuery):
    _, uuid = callback.data.split("|")
    in_memory.pending_links.pop(callback.from_user.id, None)
    in_memory.active_editors.pop(uuid, None)
    await callback.message.edit_text("❌ Отменено. Сообщение не будет сохранено.")
