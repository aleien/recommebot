import re

from aiogram import Bot, Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from fsm.states import ManualRecommend
from logic_save import check_recommendation
from logic_save import manual_recommendation
from utils.tools import extract_link

router = Router()

phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')


@router.message(StateFilter(None), Command("save"))
async def handle_save_manual(message: Message, bot: Bot, state: FSMContext):
    await manual_recommendation(message.reply_to_message, bot, state)


@router.message(StateFilter(None), F.text)
async def detect_recommendation(message: Message, bot: Bot, state: FSMContext):
    await check_recommendation(message, bot, state)
