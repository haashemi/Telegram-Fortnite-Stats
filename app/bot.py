import json
import aiohttp
import logging
from app.generateStats import GenerateStats
from aiogram.dispatcher import FSMContext
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

# Configure logging
logging.basicConfig(level=logging.INFO)

# Open and load config file
c = json.load(open("./config.json", "r"))

# Initialize bot and dispatcher
bot = Bot(token=c["TELEGRAM_BOT_TOKEN"], parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def get_url(params: dict) -> dict:
    """
    Get url then return json encoded of that

    :param params: pass parameters of the url
    :return: json encoded dictionary
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url="https://fortnite-api.com/v1/stats/br/v2", params=params) as resp:
            return await resp.json()


# _______________ Main Menu commands ________________
# ___________________________________________________
class Button():
    start_markup = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton("📊 Battle Royale Stats"),
                   types.KeyboardButton("⁉️About this bot")
                   ]],
        resize_keyboard=True)

    modes_markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [
                types.KeyboardButton("☑️ Overall"),
                types.KeyboardButton("🔴 Solo")],
            [
                types.KeyboardButton("🔵 Duos"),
                types.KeyboardButton("🟢 Squads")]
        ], resize_keyboard=True)

    back_btn = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton("↩️ Back to home")]],
        resize_keyboard=True)


btn = Button()


class Stats(StatesGroup):
    mode = State()
    username = State()


@dp.message_handler(commands="start")
async def start_menu(message: types.Message):
    await message.answer(c["t_Start"], reply_markup=btn.start_markup)


@dp.message_handler(lambda message: message.text == '↩️ Back to home', state="*")
async def back_to_home(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await message.answer(c["t_BackToHome"], reply_markup=btn.start_markup)


# _________________ START Menu BTNS _________________
# ___________________________________________________

@dp.message_handler(lambda message: message.text)
async def stats_menu(message: types.Message):

    mtext = message.text
    if mtext == '📊 Battle Royale Stats':
        await message.answer(c["t_BRStats"], reply_markup=btn.modes_markup)
        await Stats.mode.set()
    elif mtext == '⁉️About this bot':
        await message.answer(c["t_AboutBot"])


# _________________ STATS Menu BTNS _________________
# ___________________________________________________
@dp.message_handler(state=Stats.mode)
async def select_mode(message: types.Message, state: FSMContext):
    mode = {
        "☑️ Overall": "overall",
        "🔴 Solo": "solo",
        "🔵 Duos": "duo",
        "🟢 Squads": "squad"
    }

    # If sended message was in dict (☑️ Overall/ 🔴 Solo/ 🔵 Duos/ 🟢 Squads)
    if message.text in mode:
        await message.answer(c["t_SendUsername"], reply_markup=btn.back_btn)

        # Proxy the content to the next state
        async with state.proxy() as data:
            data["mode"] = mode[message.text]
            await Stats.next()
    else:
        await message.answer(c["t_BRStats"], reply_markup=btn.start_markup)
        await state.finish()


@dp.message_handler(state=Stats.username)
async def username_state(message: types.Message, state: FSMContext):
    """
    Here is the main part of the bot
    First, it gets the username from the message,
    Then use proxied content (mode) from states
    then it will do something from responses with requesting to the API
    """
    async with state.proxy() as data:
        # Get request to the API by passing some parameters
        await state.finish()
        account_params = {"name": str(message.text),
                          "accountType": "epic", "timeWindow": "lifetime"}
        resp = await get_url(account_params)

        # Do some thing with response code from API
        if resp["status"] == 404:  # It means username not Fount
            with open(f"assets/images/#not_found.png", "rb") as not_found:
                await message.answer_photo(not_found, c["t_Status404"], reply_markup=btn.start_markup)
        elif resp["status"] == 403:  # It means user stats is private
            with open(f"assets/images/#private.png", "rb") as private:
                await message.answer_photo(private, c["t_Status403"], reply_markup=btn.start_markup)
        elif resp["status"] == 200:  # It means everything should works fine
            generator = GenerateStats()  # Open #File.png then generate stats
            await generator.get_stats(message.text, data['mode'], resp["data"])
            with open(f"exports/{message.text}_{data['mode']}.png", "rb") as stats:
                await message.answer_photo(stats, c["t_Status200"].format(message.text), reply_markup=btn.start_markup)
        elif resp["status"] == 429:  # It means you requested more than maximum allowed requests
            await message.answer(c["t_Status429"], reply_markup=btn.start_markup)


def setup():
    executor.start_polling(dp, skip_updates=True)
