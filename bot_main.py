import asyncio

from aiogram import Bot, Dispatcher
from aiogram import Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from handlers import add_link
from handlers import detect
from handlers import manual
from handlers import save
from handlers import start
from utils.logger import log

# recomme-bot-bucket
bot = Bot(
    token=config.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


async def main():
    log.info("Бот запускается...")
    dp.include_router(start.router)
    dp.include_router(manual.router)
    dp.include_router(detect.router)
    dp.include_router(add_link.router)
    dp.include_router(save.router)
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
