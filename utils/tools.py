import hashlib
import re

from aiogram.types import Message
from config import recommendation_regexp

phone_pattern = re.compile(r"(\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}")
link_pattern = re.compile(r"https?://\S+")


def generate_uuid(chat_id: int, msg_id: int) -> str:
    base = f"{chat_id}:{msg_id}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]  # короткий хэш


def is_recommendation_message(message: Message) -> bool:
    link_match = extract_link(message)
    phone_match = extract_phone_from_message(message)
    text_lower = message.text.lower()
    keywords_match = re.search(recommendation_regexp, text_lower)
    if any([link_match, phone_match, keywords_match]):
        return True
    else:
        return False


def extract_link_plain(text: str, entities: []) -> str:
    if entities is not None:
        link_match = list(filter(lambda x: x.type == "url", entities))
        if link_match:
            return link_match[0].extract_from(text)
        else:
            return ""
    else:
        return ""


def extract_link(message: Message) -> str:
    return extract_link_plain(text=message.text, entities=message.entities)


def extract_phone_from_message(message: Message) -> str:
    text = message.text.lower()
    return extract_phone_from_text(text=text)


def extract_phone_from_text(text: str) -> str:
    match = phone_pattern.search(text)
    if match is not None:
        return str(phone_pattern.search(text).group(0))
    else:
        return ""


# TODO: works incorrectly
def is_recommendation_plain(text: str, entities: []) -> bool:
    text = text.lower()
    link_match = extract_link_plain(text=text, entities=entities)
    phone_match = extract_phone_from_text(text=text)
    keywords_match = re.search(recommendation_regexp, text)
    if any([link_match, phone_match, keywords_match]):
        return True
    else:
        return False
