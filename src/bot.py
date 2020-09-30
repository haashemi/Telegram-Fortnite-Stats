from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher import FSMContext
from app.utility import get_stats
from app.config import *
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# +------------------+
# |Main Menu commands|
# +------------------+
start_btns = [
    [types.KeyboardButton("📊 Battle Royale Stats"),
     types.KeyboardButton("⁉️About this bot")
     ]
]
start_markup = types.ReplyKeyboardMarkup(keyboard=start_btns, resize_keyboard=True)


@dp.message_handler(commands="start")
async def start_menu(message: types.Message):
    await message.answer(t_Start, reply_markup=start_markup)


@dp.message_handler(lambda message: message.text == '↩️ Back to home', state="*")
async def back_to_home(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await message.answer(t_BackToHome, reply_markup=start_markup)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
