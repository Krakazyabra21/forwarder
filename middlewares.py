import logging
from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
from config import config
from services import MessageForwarder

logger = logging.getLogger(__name__)


class BotMessageMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        # Фильтр ответов бота
        if event.from_user.is_bot:
            await MessageForwarder.forward_message(
                user_id=event.chat.id,
                text=event.text,
                message_id=event.message_id,
                is_bot=True
            )
        return await handler(event, data)
