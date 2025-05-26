import logging
from logging.handlers import TimedRotatingFileHandler

log = logging.getLogger()
log.setLevel(level=logging.INFO)

handler = TimedRotatingFileHandler(
    "logs/bot.log",
    when="MIDNIGHT",     # ротация каждый день
    backupCount=7        # хранить 7 дней
)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)
handler.suffix = "%Y-%m-%d"

log.addHandler(handler)
