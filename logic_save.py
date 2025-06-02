import asyncio
import os
import re

import gspread
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from oauth2client.service_account import ServiceAccountCredentials

from fsm.states import ManualRecommend
from keyboards.build_category_keyboard import build_category_keyboard
from utils.exceptions import EditorConflict
from utils.tools import generate_uuid, extract_link, extract_phone

from storage import in_memory
from utils.logger import log

phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')


async def manual_recommendation(message: Message, bot: Bot, state: FSMContext):
    if message.chat.type == "private":
        # Пропускаем личные чаты
        return

    message_text = message.text.lower()
    await reply_category(bot, message, message_text, state)


async def check_recommendation(message: Message, bot: Bot, state: FSMContext):
    if message.chat.type == "private":
        # Пропускаем личные чаты
        return

    message_text = message.text.lower()
    if extract_link(message) or bool(extract_phone(text=message_text)):
        await reply_category(bot, message, message_text, state)


async def reply_category(bot, message, message_text, state):
    log.info(f"Обнаружена рекомендация: {message_text}")
    uuid = generate_uuid(message.chat.id, message.message_id)
    in_memory.tmp_msg[uuid] = message
    # Кнопки выбора категории
    keyboard = build_category_keyboard(uuid)
    await state.set_state(ManualRecommend.selecting_category)
    reply_msg = await message.reply(
        "👀 Похоже, это рекомендация. Хотите сохранить? Выберите категорию:",
        reply_markup=keyboard
    )
    await asyncio.sleep(60)  # ждём 60 секунд
    log.info(f"Удалено сообщение с id: {reply_msg.message_id}")
    await bot.delete_message(chat_id=reply_msg.chat.id, message_id=reply_msg.message_id)


async def save_manual(bot: Bot, category, uuid, from_user_id, answer_func, edit_func):
    try:
        # Проверка: не занят ли уже кто-то другой
        if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != from_user_id:
            await answer_func("⚠️ Эту рекомендацию уже обрабатывает другой участник.", show_alert=True)
            return

        # Закрепляем текущего пользователя как “редактора”
        in_memory.active_editors[uuid] = from_user_id

        # Получаем сообщение, на которое была нажата кнопка
        orig_msg = in_memory.tmp_msg.pop(uuid)

        if not orig_msg:
            await answer_func("⚠️ Сообщение не найдено (возможно, устарело)", show_alert=True)
            in_memory.active_editors.pop(uuid, None)
            return

        name = orig_msg.from_user.username or orig_msg.from_user.first_name
        log.info(f"Сохранено сообщение от @{name}")
        log.info(f"Категория: {category}")
        log.info(f"Текст: {orig_msg.text}")

        await save_recommendation(category, name, orig_msg, uuid)

        await edit_func("✅ Рекомендация сохранена!", reply_markup=None)
        in_memory.active_editors.pop(uuid, None)

        await send_pm(bot, category, from_user_id, orig_msg)
    except Exception as error:
        log.exception(f"Ошибка при обработке callback: {error}", exc_info=True)
        await answer_func("❌ Ошибка при сохранении", show_alert=True)

def check_is_edited(uuid: str, from_user_id: str):
    is_edited = uuid in in_memory.active_editors
    is_current_editor = in_memory.active_editors[uuid] == from_user_id
    if is_edited and not is_current_editor:
        raise EditorConflict("⚠️ Эту рекомендацию уже обрабатывает другой участник.")


async def save(bot: Bot, category, uuid, from_user_id, answer_func, edit_func):
    try:
        # Проверка: не занят ли уже кто-то другой
        if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != from_user_id:
            await answer_func("⚠️ Эту рекомендацию уже обрабатывает другой участник.", show_alert=True)
            return

        # Закрепляем текущего пользователя как “редактора”
        in_memory.active_editors[uuid] = from_user_id

        # Получаем сообщение, на которое была нажата кнопка
        orig_msg = in_memory.tmp_msg.pop(uuid)

        if not orig_msg:
            await answer_func("⚠️ Сообщение не найдено (возможно, устарело)", show_alert=True)
            in_memory.active_editors.pop(uuid, None)
            return

        text = orig_msg.text.lower()
        link = extract_link(orig_msg)
        phone = extract_phone(text=text)
        has_contact = link or phone

        if not has_contact:
            in_memory.pending_links[from_user_id] = uuid  # сохраняем ожидание

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить ссылку", callback_data=f"addlink|{uuid}")],
                    [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel|{uuid}")]
                ]
            )
            await edit_func(
                "🔗 В сообщении нет ссылки или телефона.\nВы можете добавить контакт:",
                reply_markup=keyboard
            )

            return

        name = orig_msg.from_user.username or orig_msg.from_user.first_name
        log.info(f"Сохранено сообщение от @{name}")
        log.info(f"Категория: {category}")
        log.info(f"Текст: {orig_msg.text}")

        await save_recommendation(category, name, orig_msg, uuid)

        await edit_func("✅ Рекомендация сохранена!", reply_markup=None)
        in_memory.active_editors.pop(uuid, None)

        await send_pm(bot, category, from_user_id, orig_msg)
    except Exception as error:
        log.exception(f"Ошибка при обработке callback: {error}", exc_info=True)
        await answer_func("❌ Ошибка при сохранении", show_alert=True)


async def send_pm(bot, category, from_user_id, orig_msg):
    # Пробуем отправить личное уведомление
    try:
        await bot.send_message(
            chat_id=from_user_id,
            text=f"✅ Добавили рекомендацию:\n\n💬 <i>{orig_msg.text}</i>\n📂 Категория: <b>{category}</b>"
        )
    except Exception as e:
        log.warn(f"Не удалось отправить сообщение в личку: {e}", exc_info=True)


async def save_recommendation(category, name, orig_msg, uuid):
    worksheet = connect_to_gsheet(os.path.join(os.path.dirname(__file__), "credentials.json"), str(abs(orig_msg.chat.id)))
    save_to_gsheet(
        sheet=worksheet,
        uuid=uuid,
        what=f'"{orig_msg.text}"',
        category=category,
        author=name,
        date=orig_msg.date.strftime("%d.%m.%Y"),
        comment=f'"{orig_msg.text}"',
        contact=extract_contact(orig_msg),
        url=f"https://t.me/c/{orig_msg.chat.id}/{orig_msg.message_id}"
    )


def connect_to_gsheet(json_keyfile_path: str, sheet_name: str):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(sheet_name)
    return spreadsheet.sheet1


def save_to_gsheet(sheet, uuid, what, category, author, contact, comment, date, url):
    row = [uuid, what, category, author, date, contact, comment, url]
    sheet.append_row(row, value_input_option="USER_ENTERED")


def extract_contact(message: Message) -> str:
    link_match = extract_link(message)
    if link_match:
        return link_match

    return extract_phone(text=message.text)
