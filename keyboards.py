from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup


class KeyboardManager:
    @staticmethod
    def get_main_keyboard() -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()
        builder.button(text="Кнопка 1")
        builder.button(text="Кнопка 2")
        return builder.as_markup(resize_keyboard=True)