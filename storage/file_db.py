import os
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from typing import Dict

CONFIG_FILE = Path(os.path.join(os.path.dirname(__file__), 'chat_configs.json'))


@dataclass
class ChatConfig:
    chat_id: int
    channel: int
    channel_invite_link: str
    sheets_name: str
    sheets_link: str


def load_configs() -> Dict[int, ChatConfig]:
    if not CONFIG_FILE.exists():
        return {}
    raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    # Ключи в JSON — строки, приводим их обратно к int
    return {int(k): ChatConfig(**v) for k, v in raw.items()}


def save_configs(configs: Dict[int, ChatConfig]):
    # Сериализуем в JSON: ключи — строки, значения — dict
    serial = {str(k): asdict(v) for k, v in configs.items()}
    CONFIG_FILE.write_text(json.dumps(serial, ensure_ascii=False, indent=2), encoding="utf-8")


def add_or_update_config(cfg: ChatConfig):
    configs = load_configs()
    configs[cfg.chat_id] = cfg
    save_configs(configs)


def delete_config(chat_id: int):
    configs = load_configs()
    configs.pop(chat_id, None)
    save_configs(configs)

