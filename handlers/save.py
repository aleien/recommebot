import logging
import re

import gspread
from aiogram import F, Router, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from oauth2client.service_account import ServiceAccountCredentials

from storage import in_memory

router = Router()

phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')


@router.callback_query(F.data.startswith("save|"))
async def handle_save_callback(callback: CallbackQuery, bot: Bot):
    try:
        _, category, uuid = callback.data.split("|")
        # Проверка: не занят ли уже кто-то другой
        if uuid in in_memory.active_editors and in_memory.active_editors[uuid] != callback.from_user.id:
            await callback.answer("⚠️ Эту рекомендацию уже обрабатывает другой участник.", show_alert=True)
            return

        # Закрепляем текущего пользователя как “редактора”
        in_memory.active_editors[uuid] = callback.from_user.id

        # Получаем сообщение, на которое была нажата кнопка
        orig_msg = in_memory.tmp_msg.pop(uuid)

        if not orig_msg:
            await callback.answer("⚠️ Сообщение не найдено (возможно, устарело)", show_alert=True)
            in_memory.active_editors.pop(uuid, None)
            return

        text = orig_msg.text.lower()
        has_link = list(filter(lambda x: x.type == 'url', orig_msg.entities))
        has_phone = bool(phone_pattern.search(text))
        has_contact = has_link or has_phone

        if not has_contact:
            in_memory.pending_links[callback.from_user.id] = uuid  # сохраняем ожидание

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить ссылку", callback_data=f"addlink|{uuid}")],
                    [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel|{uuid}")]
                ]
            )
            await callback.message.edit_text(
                "🔗 В сообщении нет ссылки или телефона.\nВы можете добавить контакт:",
                reply_markup=keyboard
            )

            return

        # Здесь можно подключить сохранение в Google Sheet, БД и т.п.
        name = orig_msg.from_user.username or orig_msg.from_user.first_name
        logging.info(f"Сохранено сообщение от @{name}")
        logging.info(f"Категория: {category}")
        logging.info(f"Текст: {orig_msg.text}")

        worksheet = connect_to_gsheet("credentials.json", "mamy2024")
        save_recommendation(
            sheet=worksheet,
            what=f'"{orig_msg.text}"',
            category=category,
            author=name,
            date=orig_msg.date.strftime("%d.%m.%Y"),
            comment=f'"{orig_msg.text}"',
            contact=extract_contact(orig_msg) or "",
            url=f"https://t.me/c/{orig_msg.chat.id}/{orig_msg.message_id}"
        )

        await callback.message.edit_text("✅ Рекомендация сохранена!", reply_markup=None)
        in_memory.active_editors.pop(uuid, None)

        # Пробуем отправить личное уведомление
        try:
            await bot.send_message(
                chat_id=callback.from_user.id,
                text=f"✅ Добавили рекомендацию:\n\n💬 <i>{orig_msg.text}</i>\n📂 Категория: <b>{category}</b>"
            )
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение в личку: {e}", exc_info=True)

    except Exception as error:
        logging.exception(f"Ошибка при обработке callback: {error}", exc_info=True)
        await callback.answer("❌ Ошибка при сохранении", show_alert=True)


def connect_to_gsheet(json_keyfile_path: str, sheet_name: str):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, scope)
    client = gspread.authorize(credentials)
    spreadsheet = client.open(sheet_name)
    return spreadsheet.sheet1


def save_recommendation(sheet, what, category, author, contact, comment, date, url):
    row = [what, category, author, contact, comment, date, url]
    sheet.append_row(row, value_input_option="USER_ENTERED")


def extract_contact(message: Message) -> str:
    link_match = list(filter(lambda x: x.type == 'url', message.entities))
    if link_match:
        return link_match[0].extract_from(message.text)

    phone_match = phone_pattern.search(message.text)
    if phone_match:
        return phone_match.group(0)

    return ""
