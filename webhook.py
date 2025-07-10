from fastapi import FastAPI, Request
from aiogram import Bot, Dispatcher
from config import config

app = FastAPI()


class WebhookManager:
    def __init__(self, bot: Bot, dp: Dispatcher):
        self.bot = bot
        self.dp = dp

    async def setup_webhook(self):
        await self.bot.set_webhook(
            url=config.WEBHOOK_URL,
            drop_pending_updates=True
        )

    @app.post("/")
    async def telegram_webhook(self, update: dict):
        await self.dp.feed_update(bot=self.bot, update=update)
        return {"status": "ok"}

    @app.post("/webhook")
    async def smarty_webhook(self, request: Request):
        payload = await request.json()
        # Логика обработки входящих сообщений от Smarty
        return {"status": "ok"}