import httpx
import logging
from config import config
from aiogram.types import Message

logger = logging.getLogger(__name__)


class MessageForwarder:
    @staticmethod
    async def forward_message(message: Message):
        data = message.dict()
        # print(message)
        try:
            timeout = httpx.Timeout(10.0, connect=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(config.FORWARD_URL, json=data)
                response.raise_for_status()
                logger.info(f"Сообщение переслано | URL: {config.FORWARD_URL} | Статус: {response.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Ошибка пересылки: {str(e)} | URL: {config.FORWARD_URL}")
        except Exception as e:
            logger.exception("Непредвиденная ошибка при пересылке:")