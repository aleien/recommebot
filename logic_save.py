import asyncio
import os

import gspread
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram import html
from aiogram.methods import CopyMessage
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup, LinkPreviewOptions
)

import config
from config import settings, environment_config, category_tags
from oauth2client.service_account import ServiceAccountCredentials

from fsm.states import ManualRecommend
from keyboards.build_category_keyboard import build_category_keyboard
from storage.file_db import ChatConfig
from utils.exceptions import EditorConflict
from utils.tools import generate_uuid, extract_link, extract_phone_from_text, extract_link_plain

from storage import in_memory
from utils.logger import log


async def manual_recommendation(message: Message, bot: Bot, state: FSMContext):
    if message.chat.type == "private":
        # Пропускаем личные чаты
        return

    await reply_category(bot, message, state)


async def check_recommendation(message: Message, bot: Bot, state: FSMContext):
    if message.chat.type == "private":
        # Пропускаем личные чаты
        return

    message_text = message.text.lower()
    if extract_link(message) or bool(extract_phone_from_text(text=message_text)):
        await reply_confirmation(bot, message, message_text)


async def reply_confirmation(bot, message, message_text):
    log.info(f"Обнаружена рекомендация: {message_text}")
    uuid = generate_uuid(message.chat.id, message.message_id)
    in_memory.tmp_msg[uuid] = message

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm|{uuid}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"cancel|{uuid}")
        ]
    ])

    reply_msg = await message.reply(
        "👀 Похоже, это рекомендация. Хотите сохранить?",
        reply_markup=keyboard
    )
    in_memory.confirmation_msgs[uuid] = reply_msg.message_id

    await asyncio.sleep(60)
    try:
        await bot.delete_message(chat_id=reply_msg.chat.id, message_id=reply_msg.message_id)
    except TelegramBadRequest:
        pass


async def confirm_callback(uuid, user_id, bot, chat_id, answer_func, reply_func):
    # Защита от параллельного редактирования
    if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != user_id:
        await answer_func("⚠️ Уже обрабатывается другим участником.", show_alert=True)
        return

    in_memory.active_editors[uuid] = user_id

    # Удалить сообщение подтверждения
    msg_id = in_memory.confirmation_msgs.pop(uuid, None)
    if msg_id:
        try:
            await bot.delete_message(chat_id, msg_id)
        except TelegramBadRequest:
            pass

    # Показать категории
    keyboard = build_category_keyboard(uuid)
    await reply_func.reply(
        "📂 Выберите категорию:",
        reply_markup=keyboard
    )
    await answer_func()


async def reply_category(bot, message, state):
    message_text = message.text if message.text else (message.caption if message.caption else message.message_id)
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

    state.clear()
    in_memory.tmp_msg.pop(uuid)
    in_memory.active_editors.pop(uuid)
    await bot.delete_message(chat_id=reply_msg.chat.id, message_id=reply_msg.message_id)


def check_is_edited(uuid: str, from_user_id: str):
    is_edited = uuid in in_memory.active_editors
    is_current_editor = in_memory.active_editors[uuid] == from_user_id
    if is_edited and not is_current_editor:
        raise EditorConflict("⚠️ Эту рекомендацию уже обрабатывает другой участник.")


async def save(bot: Bot, category, uuid, from_user_id, answer_func, edit_func, state):
    try:
        # Проверка: не занят ли уже кто-то другой
        if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != from_user_id:
            await answer_func("⚠️ Эту рекомендацию уже обрабатывает другой участник.", show_alert=True)
            return

        log.info(f"Сохраняем uuid={uuid}, editor_id={from_user_id}")
        # Закрепляем текущего пользователя как “редактора”
        in_memory.active_editors[uuid] = from_user_id

        # Получаем сообщение, на которое была нажата кнопка
        orig_msg: Message = in_memory.tmp_msg.pop(uuid)

        if not orig_msg:
            await answer_func("⚠️ Сообщение не найдено (возможно, устарело)", show_alert=True)
            in_memory.active_editors.pop(uuid, None)
            return

        name = orig_msg.from_user.username or orig_msg.from_user.first_name

        log.info(f"Сохранено сообщение от @{name}")
        log.info(f"Категория: {category}")

        if orig_msg.photo or orig_msg.document:
            log.info(f"Фото/файл")
        else:
            log.info(f"Текст: {orig_msg.text}")

        category_tag = category_tags[category]
        log.info(f"Получаем конфиг чата: {orig_msg.chat.id}")
        chat_config = config.chat_configs[orig_msg.chat.id]

        if not chat_config:
            await answer_func("⚠️ Сообщение не найдено (возможно, устарело)", show_alert=True)
            in_memory.active_editors.pop(uuid, None)
            return

        copy: CopyMessage = await save_media_recommendation(category_tag, orig_msg, uuid, bot, chat_config)
        message_link = f"https://t.me/c/{chat_config.channel}/{copy.message_id}"
        html_link = html.link("сохранена", message_link)
        sheet_link = html.link("Таблица", chat_config.sheets_link)
        invite_link = html.link("Доступ в канал сохраненок", chat_config.channel_invite_link)
        await edit_func(
            f"✅ Рекомендация {html_link}! \n\n🗒{sheet_link} | 🔗{invite_link}",
            reply_markup=None,
            link_preview_options=LinkPreviewOptions(is_disabled=True)
        )
        await save_gsheet_recommendation(category, name, orig_msg, uuid, message_link, chat_config)

        in_memory.active_editors.pop(uuid, None)
        if state is not None:
            await state.clear()

    except Exception as error:
        log.exception(f"Ошибка при обработке callback: {error}", exc_info=True)
        await answer_func("❌ Ошибка при сохранении", show_alert=True)


async def save_media_recommendation(category: str, message: Message, uuid, bot: Bot, chat_config: ChatConfig) -> CopyMessage:
    log.info(f"Обнаружена рекомендация с медиа, uuid={uuid}")
    edited_caption = f"{message.caption}\n\n#{category}" if message.caption else f"#{category}"
    edited_text = f"{message.text}\n\n#{category}" if message.text else f"#{category}"

    channel_id = f"-100{chat_config.channel}"
    if len(edited_caption) >= 1024:
        tag_caption = f"#{category}"
        extra_text = message.caption
        copy = await message.copy_to(
            chat_id=channel_id,
            caption=tag_caption,
            disable_notification=True
        )
        await bot.send_message(channel_id, text=extra_text, disable_notification=True)
    else:
        copy = await message.copy_to(
            chat_id=channel_id,
            disable_notification=True
        )

    if message.caption:
        await bot.edit_message_caption(caption=edited_caption, chat_id=channel_id)
    if message.text:
        await bot.edit_message_text(
            text=edited_text,
            message_id=copy.message_id,
            chat_id=channel_id
        )
    return copy


async def save_gsheet_recommendation(category, name, orig_msg, uuid, message_link, chat_config: ChatConfig):
    worksheet = connect_to_gsheet(os.path.join(os.path.dirname(__file__), "credentials.json"), chat_config.sheets_name)

    if orig_msg.text:
        contact = extract_contact_plain(orig_msg.text, orig_msg.entities)
        comment = orig_msg.text
    elif orig_msg.caption:
        contact = extract_contact_plain(orig_msg.caption, orig_msg.caption_entities)
        comment = orig_msg.caption
    else:
        contact = ""
        comment = ""

    save_to_gsheet(
        sheet=worksheet,
        uuid=uuid,
        what=f'"{comment}"',
        category=category,
        author=name,
        date=orig_msg.date.strftime("%d.%m.%Y"),
        comment="",
        contact=contact,
        url=message_link,
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
    row = [uuid,  date,  what, category, author,contact, comment, url]
    sheet.append_row(row, value_input_option="USER_ENTERED")


def extract_contact(message: Message) -> str:
    link_match = extract_link(message)
    if link_match:
        return link_match

    phone = extract_phone_from_text(text=message.text)
    if phone:
        return f"'{phone}"
    else:
        return ""


def extract_contact_plain(text: str, entities: []) -> str:
    link_match = extract_link_plain(text, entities)
    if link_match:
        return link_match

    phone = extract_phone_from_text(text=text)
    if phone:
        return f"'{phone}"
    else:
        return ""
