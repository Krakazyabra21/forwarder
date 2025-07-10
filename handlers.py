from aiogram import F
from aiogram.types import Message
from aiogram.filters import CommandStart
from keyboards import KeyboardManager
from services import MessageForwarder


class MessageHandlers:
    @staticmethod
    async def _forward_and_respond(message: Message, response_text: str = None):
        # print(update)
        if response_text:
            await message.answer(response_text)
        await MessageForwarder.forward_message(message)

    @staticmethod
    async def cmd_start(message: Message):
        await message.answer(
            "Привет, жми кнопки",
            reply_markup=KeyboardManager.get_main_keyboard()
        )

    @staticmethod
    async def button_handler(message: Message):
        button_text = message.text
        response = f"Вы нажали на {button_text}"
        await MessageHandlers._forward_and_respond(message, response)

    @staticmethod
    async def text_messages(message: Message):
        await MessageHandlers._forward_and_respond(message)

def register_handlers(dp):
    dp.message.register(MessageHandlers.cmd_start, CommandStart())
    dp.message.register(MessageHandlers.button_handler, F.text.in_(["Кнопка 1", "Кнопка 2"]))
    dp.message.register(MessageHandlers.text_messages, F.text)