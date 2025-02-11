import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    "app.log", maxBytes=10**6, backupCount=5  # Размер файла 1МБ, до 5 резервных копий
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        handler,
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)