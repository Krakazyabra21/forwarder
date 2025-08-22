import logging
import ssl
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from aiogram.filters import Command

# Настройки
API_TOKEN = '7498645289:AAHOQFCFiwMke-hm9U0wdDRucR0nj19Y3t4'
WEBHOOK_HOST = 'https://your.domain.com'  # Ваш домен
WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEBAPP_HOST = 'localhost'
WEBAPP_PORT = 3001

# Инициализация бота и диспетчера
main_bot = Bot(token=API_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.reply("Привет! Я бот с вебхуком!")


@dp.message()
async def echo(message: types.Message):
    await message.answer(message.text)


async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info("Бот запущен и вебхук установлен")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    logging.info("Вебхук удален")


def main(bot: Bot):
    logging.basicConfig(level=logging.INFO)
    app = web.Application()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )

    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain('/path/to/fullchain.pem', '/path/to/privkey.pem')

    setup_application(app, dp, bot=bot)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT, ssl_context=context)


if __name__ == '__main__':
    main(main_bot)
