import hashlib


def generate_uuid(chat_id: int, msg_id: int) -> str:
    base = f"{chat_id}:{msg_id}"
    return hashlib.sha256(base.encode()).hexdigest()[:12]  # короткий хэш