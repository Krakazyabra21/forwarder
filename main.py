import logging
import json
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiohttp import web
import asyncio
import aiohttp
import requests

# Настройки
TOKEN_API = '7484036286:AAFG0lRZbs9OJftLIR_4Pbu_E1kJ7yJWvKQ'
smarty_url: str = ""
# local_url = "https://blithely-feasible-loon.cloudpub.ru"
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
    logger.info("🌐 Webhook endpoint called")
    try:
        update = types.Update(**await request.json())
        await dp.feed_update(bot=main_bot, update=update)
        if smarty_url:
            response = requests.post(smarty_url, json=await request.json())
            logger.info(f"Response Smarty: {response.status_code}")
        else:
            logger.warning(f"⚠️ NO SMARTY URL ⚠️")
        return web.Response()
    except Exception as e:
        logger.warning(f"Console-Error:  {e}")
        return web.Response(status=403)


async def set_webhook_handler(request):
    global smarty_url
    try:
        data = await request.json()
        webhook_url = data.get('url')
        if not webhook_url:
            return web.Response(
                text=json.dumps({'error': 'webhook_url is required'}),
                status=400,
                content_type='application/json'
            )
        smarty_url = webhook_url
        return web.Response(
            text=json.dumps({"ok": True, "result": True, "description": "Webhook was set"}),
            status=200,
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Error setting webhook: {e}")
        return web.Response(
            text=json.dumps({"ok": False, "error_code": 400, "description": "Bad Request: wrong url"}),
            status=400,
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
    global smarty_url
    try:
        webhook_info = await main_bot.get_webhook_info()
        logger.info(f"📋 Current webhook info: {webhook_info}")

        response_data = {
            'url': smarty_url,
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
    global smarty_url
    try:
        me = await main_bot.get_me()
        logger.info(f"🤖 Bot info: {me.username} (ID: {me.id})")

        response_data = {
            'status': 'healthy',
            'bot_username': me.username,
            'bot_id': me.id,
            'webhook_configured': False,
            'timestamp': time.time()
        }

        webhook_info = await main_bot.get_webhook_info()
        if webhook_info.url and smarty_url:
            response_data['webhook_configured'] = True
            response_data['webhook_url'] = smarty_url
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


async def get_user_profile_photos_handler(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        limit = data.get('limit', 1)

        if not user_id:
            return web.Response(
                text=json.dumps({'error': 'user_id is required'}),
                status=400,
                content_type='application/json'
            )

        logger.info(f"🖼 GET USER PROFILE PHOTOS: Request for user {user_id}, limit {limit}")

        profile_photos = await main_bot.get_user_profile_photos(user_id, limit=limit)

        photos_data = []
        for photo_group in profile_photos.photos:
            group_data = []
            for photo in photo_group:
                file_info = await main_bot.get_file(photo.file_id)
                photo_info = {
                    'file_id': photo.file_id,
                    'file_unique_id': photo.file_unique_id,
                    'width': photo.width,
                    'height': photo.height,
                    'file_size': photo.file_size,
                    'file_path': file_info.file_path
                }
                group_data.append(photo_info)
            photos_data.append(group_data)

        response_data = {
            'total_count': profile_photos.total_count,
            'photos': photos_data
        }

        return web.Response(
            text=json.dumps(response_data, indent=2),
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Error getting user profile photos: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def get_file_handler(request):
    try:
        data = await request.json()
        file_id = data.get('file_id')

        if not file_id:
            return web.Response(
                text=json.dumps({'error': 'file_id is required'}),
                status=400,
                content_type='application/json'
            )

        logger.info(f"📁 GET FILE: Request for file {file_id}")

        file_info = await main_bot.get_file(file_id)

        response_data = {
            'file_id': file_info.file_id,
            'file_unique_id': file_info.file_unique_id,
            'file_size': file_info.file_size,
            'file_path': file_info.file_path
        }

        return web.Response(
            text=json.dumps(response_data, indent=2),
            content_type='application/json'
        )

    except Exception as e:
        logger.error(f"❌ Error getting file info: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500,
            content_type='application/json'
        )


async def forward_file_handler(request):
    try:
        file_path = request.match_info['file_path']
        logger.info(f"📥 Forwarding file: {file_path}")

        telegram_file_url = f'https://api.telegram.org/file/bot{TOKEN_API}/{file_path}'

        async with aiohttp.ClientSession() as session:
            async with session.get(telegram_file_url) as resp:
                if resp.status == 200:
                    # Просто передаем данные как есть, без указания content_type
                    file_data = await resp.read()
                    return web.Response(body=file_data)
                else:
                    return web.Response(
                        text=f"Error downloading file: {resp.status}",
                        status=resp.status
                    )

    except Exception as e:
        logger.error(f"❌ Error forwarding file: {e}")
        return web.Response(
            text=json.dumps({'error': str(e)}),
            status=500
        )


async def test_handler(request):
    return web.Response(
        text=json.dumps({'message': 'Server is running', 'timestamp': time.time()}),
        content_type='application/json'
    )


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


# Регистрация обработчиков
app.router.add_post(f'/forwarder/{TOKEN_API}', handle_webhook)
app.router.add_post('/forwarder/setWebhook', set_webhook_handler)
app.router.add_get('/forwarder/getMe', health_check_handler)
app.router.add_get('/forwarder/test', test_handler)
app.router.add_post('/forwarder/getUserProfilePhotos', get_user_profile_photos_handler)
app.router.add_post('/forwarder/getFile', get_file_handler)
app.router.add_get('/forwarder/{file_path:.+}', forward_file_handler)

if __name__ == '__main__':
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    logger.info("🌐 Starting web server on 127.0.0.1:8000")
    web.run_app(
        app,
        host='127.0.0.1',
        port=8000
    )