import hashlib
import re

from aiogram.types import Message

phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')


def generate_uuid(chat_id: int, msg_id: int) -> str:
    base = f"{chat_id}:{msg_id}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]  # короткий хэш


# TODO: multiple links
def extract_link(message: Message) -> str:
    if message.entities is not None:
        link_match = list(filter(lambda x: x.type == 'url', message.entities))
        if link_match:
            return link_match[0].extract_from(message.text)
        else: return ""
    else:
        return ""


def extract_phone(message: Message) -> str:
    text = message.text.lower()
    return extract_phone(text=text)


def extract_phone(text: str) -> str:
    match = phone_pattern.search(text)
    if match is not None:
        return str(phone_pattern.search(text).group(0))
    else:
        return ""
