import hashlib

from aiogram.types import Message


def generate_uuid(chat_id: int, msg_id: int) -> str:
    base = f"{chat_id}:{msg_id}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]  # короткий хэш


# TODO: multiple links
def extract_link(message: Message) -> str:
    link_match = list(filter(lambda x: x.type == 'url', message.entities))
    if link_match:
        return link_match[0].extract_from(message.text)
    else:
        return ""
