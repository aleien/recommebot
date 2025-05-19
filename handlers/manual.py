from aiogram import Router, Bot
from aiogram.filters import Command
from aiogram.types import Message

from utils.tools import generate_uuid
from storage import in_memory

router = Router()


@router.message(Command("save"))
@router.message(Command("✍️"))
async def handle_save_manual(message: Message, bot: Bot):
    uuid = generate_uuid(message.chat.id, message.message_id)
    if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != message.from_user.id:
        await message.answer("⚠️ Эту рекомендацию уже обрабатывает другой участник.", show_alert=True)
        return

    # Закрепляем текущего пользователя как “редактора”
    in_memory.active_editors[uuid] = message.from_user.id
    text = message.text.lower()
    await message.answer("Учусь сохранять...")

