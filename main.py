import logging
import json
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web
import asyncio
import requests

# Настройки
TOKEN_API = '7484036286:AAFG0lRZbs9OJftLIR_4Pbu_E1kJ7yJWvKQ'
SMARTY_URL: str
local_url = "https://smartybotapps.ru/forwarder"
# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

main_bot = Bot(token=TOKEN_API)
dp = Dispatcher()
app = web.Application()


# Обработчики сообщений
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    logger.info(f"🎯 START COMMAND: Received /start from user {message.from_user.id} (@{message.from_user.username})")
    builder = ReplyKeyboardBuilder()
    builder.add(types.KeyboardButton(text="Кнопка 1"))
    builder.add(types.KeyboardButton(text="Кнопка 2"))

    try:
        await message.answer(
            "Привет, жми кнопки",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
        logger.info("✅ Successfully sent welcome message")
    except Exception as e:
        logger.error(f"❌ Error sending welcome message: {e}")


@dp.message(F.text.in_(["Кнопка 1", "Кнопка 2"]))
async def handle_button(message: types.Message):
    logger.info(f"🔘 BUTTON: Received button '{message.text}' from user {message.from_user.id}")
    button_number = message.text.split()[1]

    try:
        await message.answer(f"Вы нажали на кнопку {button_number}")
        logger.info(f"✅ Successfully responded to button {button_number}")
    except Exception as e:
        logger.error(f"❌ Error responding to button: {e}")


@dp.message()
async def echo_message(message: types.Message):
    logger.info(
        f"💬 MESSAGE: Received text '{message.text}' from user {message.from_user.id} (@{message.from_user.username})")

    try:
        await message.answer(f"Вы сказали: {message.text}")
        logger.info("✅ Successfully echoed message")
    except Exception as e:
        logger.error(f"❌ Error echoing message: {e}")


async def handle_webhook(request):
    global SMARTY_URL
    logger.info("🌐 Webhook endpoint called")

    try:
        update = types.Update(**await request.json())
        # print(update)
        await dp.feed_update(bot=main_bot, update=update)
        if SMARTY_URL:
            response = requests.post(SMARTY_URL, request.json())
            logger.info(f"Response Smarty: {response.status_code}")
        else:
            logger.warning(f"⚠️ NO SMARTY URL ⚠️")
        return web.Response()
    except:
        return web.Response(status=403)


async def set_webhook_handler(request):
    global SMARTY_URL
    try:
        data = await request.json()
        webhook_url = data.get('webhook_url')
        SMARTY_URL = webhook_url
        if not webhook_url:
            return web.Response(
                text=json.dumps({'error': 'webhook_url is required'}),
                status=400,
                content_type='application/json'
            )

    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def delete_webhook_handler(request):
    try:
        result = await main_bot.delete_webhook(drop_pending_updates=True)
        logger.info(f"🗑️ Webhook deletion result: {result}")

        response_data = {
            'success': result,
            'message': 'Webhook deleted successfully' if result else 'Failed to delete webhook'
        }

        return web.Response(
            text=json.dumps(response_data, indent=2),
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Error deleting webhook: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def get_webhook_info_handler(request):
    try:
        webhook_info = await main_bot.get_webhook_info()
        logger.info(f"📋 Current webhook info: {webhook_info}")

        response_data = {
            'url': webhook_info.url,
            'has_custom_certificate': webhook_info.has_custom_certificate,
            'pending_update_count': webhook_info.pending_update_count,
            'ip_address': webhook_info.ip_address,
            'last_error_date': webhook_info.last_error_date.timestamp() if webhook_info.last_error_date else None,
            'last_error_message': webhook_info.last_error_message,
            'max_connections': webhook_info.max_connections,
            'allowed_updates': webhook_info.allowed_updates
        }

        return web.Response(
            text=json.dumps(response_data, indent=2),
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Error getting webhook info: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def health_check_handler(request):
    try:
        # Проверяем, что бот работает
        me = await main_bot.get_me()
        logger.info(f"🤖 Bot info: {me.username} (ID: {me.id})")

        response_data = {
            'status': 'healthy',
            'bot_username': me.username,
            'bot_id': me.id,
            'webhook_configured': False,
            'timestamp': time.time()
        }

        # Проверяем информацию о вебхуке
        webhook_info = await main_bot.get_webhook_info()
        if webhook_info.url:
            response_data['webhook_configured'] = True
            response_data['webhook_url'] = webhook_info.url
            response_data['pending_updates'] = webhook_info.pending_update_count
            response_data['last_error'] = webhook_info.last_error_message

        return web.Response(
            text=json.dumps(response_data, indent=2),
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return web.Response(
            text=json.dumps({'status': 'unhealthy', 'error': str(e)}),
            status=500,
            content_type='application/json'
        )


# Тестовый endpoint для проверки сервера
async def test_handler(request):
    return web.Response(
        text=json.dumps({'message': 'Server is running', 'timestamp': time.time()}),
        content_type='application/json'
    )


# Тестовый endpoint для проверки обработчиков
async def test_update_handler(request):
    try:
        test_update = {
            "update_id": 999999,
            "message": {
                "message_id": 1,
                "date": int(time.time()),
                "chat": {"id": 714348748, "type": "private"},
                "from": {
                    "id": 714348748,
                    "first_name": "TestUser",
                    "is_bot": False
                },
                "text": "/start"
            }
        }

        logger.info("🧪 Processing test update...")

        update = types.Update.model_validate(test_update)
        await dp.feed_update(bot=main_bot, update=update)

        return web.Response(
            text=json.dumps({'message': 'Test update processed', 'update': test_update}, indent=2),
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Test update error: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def on_startup(_):
    logger.info("🚀 Бот запущен")
    try:
        await main_bot.set_webhook(f"{local_url}/{TOKEN_API}")
        logger.info("Вебхук создан")
    except Exception as e:
        logger.warning(f"❌❌❌ {e}")
    try:
        me = await main_bot.get_me()
        logger.info(f"🤖 Bot verified: @{me.username} (ID: {me.id})")
    except Exception as e:
        logger.error(f"❌ Bot verification failed: {e}")

    try:
        webhook_info = await main_bot.get_webhook_info()
        logger.info(f"📋 Current webhook: {webhook_info.url or 'Not set'}")
        if webhook_info.pending_update_count > 0:
            logger.warning(f"⚠️ Pending updates: {webhook_info.pending_update_count}")
        if webhook_info.last_error_message:
            logger.warning(f"⚠️ Last webhook error: {webhook_info.last_error_message}")
    except Exception as e:
        logger.error(f"❌ Error checking webhook: {e}")


async def on_shutdown(_):
    logger.info("🛑 Shutting down...")
    try:
        await main_bot.delete_webhook()
        await main_bot.session.close()
        logger.info("🗑️ Webhook deleted on shutdown")
    except Exception as e:
        logger.error(f"❌ Error deleting webhook on shutdown: {e}")


print(f"{local_url}/{TOKEN_API}")

app.router.add_post(f'/forwarder/{TOKEN_API}', handle_webhook)  # Webhook endpoint
app.router.add_post('/forwarder/set_webhook', set_webhook_handler)
# app.router.add_post('/delete_webhook', delete_webhook_handler)
# app.router.add_get('/webhook_info', get_webhook_info_handler)
# app.router.add_get('/health', health_check_handler)
app.router.add_get('/forwarder/test', test_handler)
# app.router.add_post('/test_update', test_update_handler)

if __name__ == '__main__':
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logger.info("🌐 Starting web server on 127.0.0.1:4433")
    web.run_app(
        app,
        host='127.0.0.1',
        port=4433
    )
