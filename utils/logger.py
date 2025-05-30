import logging
import os
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger()
log.setLevel(level=logging.INFO)

LOG_FILE = os.path.join(os.path.dirname(__file__), "../logs/bot.log")
handler = TimedRotatingFileHandler(
    LOG_FILE,
    when="MIDNIGHT",     # ротация каждый день
    backupCount=7        # хранить 7 дней
)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
handler.suffix = "%Y-%m-%d"

log.addHandler(handler)
