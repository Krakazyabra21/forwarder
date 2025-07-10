import json
import logging
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from aiogram import Bot, Dispatcher, types
from config import config
from handlers import register_handlers
from middlewares import BotMessageMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Определяем режим работы (HTTPS для продакшена, HTTP для разработки)
IS_PRODUCTION = config.WEBHOOK_URL.startswith("https://")

# Создаем объекты бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Регистрация middleware
dp.message.outer_middleware(BotMessageMiddleware())

# Регистрация обработчиков
register_handlers(dp)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запускаем поллинг бота в фоновом режиме
    polling_task = asyncio.create_task(dp.start_polling(bot))
    logger.info("Бот запущен в режиме поллинга")

    yield

    # Останавливаем бота при завершении
    await dp.stop_polling()
    await polling_task
    logger.info("Бот остановлен")


app = FastAPI(lifespan=lifespan)


@app.post("/external_webhook")
async def handle_external_webhook(request: Request):
    """Эндпоинт для обработки внешних вебхуков"""
    try:
        # Парсим входящий вебхук
        data = await request.json()
        logger.info(f"Получен внешний вебхук: {data}")

        # Здесь ваша логика обработки вебхука
        # Например, отправка сообщения через бота
        user_id = data.get("user_id")
        message = data.get("message")

        if user_id and message:
            await bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Сообщение отправлено пользователю {user_id}")

        return {"status": "success", "data": data}

    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/send_message")
async def send_message_endpoint(request: Request):
    """Кастомный эндпоинт для отправки сообщений"""
    try:
        # print(json.dumps(data, indent=2))
        data = await request.json()

        user_id = data["from_user"]["id"]
        text = data.get("text", "")

        message = f"Ваше сообщение: {text}"

        if not user_id or not text:
            raise ValueError("Отсутствуют user_id или text")

        await bot.send_message(chat_id=user_id, text=message)
        logger.info(f"Сообщение отправлено пользователю {user_id}: {text}")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=config.WEB_SERVER_HOST,
        port=config.WEB_SERVER_PORT,
        reload=config.RELOAD
    )