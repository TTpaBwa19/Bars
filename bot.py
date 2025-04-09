from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "7810631158:AAFZnfH_Y1Bfai_pJ-SyWshFwyKZICf-w18"
WEB_APP_URL = "https://ttpabwa19.github.io/Bars/"  # Ссылка на твоё мини-приложение

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer(
        "🎮 BarsIQ - мини-игра для прокачки мозга!\nНажми кнопку ниже, чтобы начать:",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton(
                text="🧠 Играть в BarsIQ", 
                web_app=types.WebAppInfo(url=WEB_APP_URL)
            )
        )
    )

if __name__ == '__main__':
    executor.start_polling(dp)
