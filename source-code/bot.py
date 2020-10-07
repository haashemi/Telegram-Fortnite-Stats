import json
import aiohttp
import logging
from aiogram.dispatcher import FSMContext
from PIL import Image, ImageFont, ImageDraw
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
c = json.load(open("./config.json", "r"))
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


class GenerateStats:
    """
    Class of everything that needed to make the Stats image
    """

    def __init__(self) -> None:
        """
        Open/Ready necessary things
        """
        self.stats = Image.open("assets/#file.png")
        self.draw = ImageDraw.Draw(self.stats)
        self.font = ImageFont.truetype(
            r"assets/fonts/BurbankBigCondensed-Black.ttf", 60)

    async def draw_on(self, position: tuple, text, color: tuple = None) -> None:
        """
        Draw some text on specific posotion of image

        :param position: Position of text (x, y)
        :param text: Any text you want to draw on image (int/float/str)
        :param color: RGB Color of text (R, G, B)
        """
        color = color if color is not None else (255, 255, 255)
        self.draw.text(position, str(text), color, self.font)

    async def get_stats(self, username, mode: str, data: dict) -> None:
        """
        Make an Image of player stats, main thing happens here

        :param username: Username of player
        :param mode: Game mode (overall/solo/duo/squad)
        :param data: Collected json data from API
        """
        await self.draw_on((140, 155), data["account"]["name"])
        await self.draw_on((785, 155),
                           str(data["battlePass"]["level"]) + "." + str(data["battlePass"]["progress"]))
        await self.draw_on((140, 400), data["stats"]["all"][mode]["wins"])

        if mode == "overall" or mode == "solo":
            await self.draw_on((590, 310), "10", (243, 239, 255))
            await self.draw_on((535, 400), data["stats"]["all"][mode]["top10"])
            await self.draw_on((990, 310), "25", (243, 239, 255))
            await self.draw_on((930, 400), data["stats"]["all"][mode]["top25"])
        elif mode == "duo":
            await self.draw_on((590, 310), "5", (243, 239, 255))
            await self.draw_on((535, 400), data["stats"]["all"][mode]["top5"])
            await self.draw_on((990, 310), "12", (243, 239, 255))
            await self.draw_on((930, 400), data["stats"]["all"][mode]["top12"])
        elif mode == "squad":
            await self.draw_on((590, 310), "3", (243, 239, 255))
            await self.draw_on((535, 400), data["stats"]["all"][mode]["top3"])
            await self.draw_on((990, 310), "5", (243, 239, 255))
            await self.draw_on((930, 400), data["stats"]["all"][mode]["top6"])

        await self.draw_on((140, 650), data["stats"]["all"][mode]["kills"])
        await self.draw_on((535, 650), data["stats"]["all"][mode]["killsPerMatch"])
        await self.draw_on((930, 650), data["stats"]["all"][mode]["kd"])
        await self.draw_on((140, 905), data["stats"]["all"][mode]["matches"])
        await self.draw_on((930, 905), data["stats"]["all"][mode]["winRate"])
        await self.draw_on((140, 1140), data["stats"]["all"][mode]["minutesPlayed"])
        await self.draw_on((785, 1140), mode.upper())

        self.stats.save(f"exports/{username}_{mode}.png")


# _______________ Main Menu commands ________________
# ___________________________________________________

start_markup = types.ReplyKeyboardMarkup(
    keyboard=[[types.KeyboardButton("📊 Battle Royale Stats"),
               types.KeyboardButton("⁉️About this bot")
               ]],
    resize_keyboard=True)


@dp.message_handler(commands="start")
async def start_menu(message: types.Message):
    await message.answer(c["t_Start"], reply_markup=start_markup)


@dp.message_handler(lambda message: message.text == '↩️ Back to home', state="*")
async def back_to_home(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await message.answer(c["t_BackToHome"], reply_markup=start_markup)


# _________________ START Menu BTNS _________________
# ___________________________________________________

class Stats(StatesGroup):
    mode = State()
    username = State()


@dp.message_handler(lambda message: message.text == "📊 Battle Royale Stats")
async def stats_menu(message: types.Message):
    modes_markup = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton("☑️ Overall"),
             types.KeyboardButton("🔴 Solo")],
            [types.KeyboardButton("🔵 Duos"),
             types.KeyboardButton("🟢 Squads")]
        ], resize_keyboard=True)

    await message.answer(c["t_BRStats"], reply_markup=modes_markup)
    await Stats.mode.set()


@dp.message_handler(lambda message: message.text == "⁉️About this bot")
async def about_bot(message: types.Message):
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

    back_btn = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton("↩️ Back to home")]],
        resize_keyboard=True)

    # If sended message was in dict (☑️ Overall/ 🔴 Solo/ 🔵 Duos/ 🟢 Squads)
    if message.text in mode:
        await message.answer(c["t_SendUsername"], reply_markup=back_btn)

        # Proxy the content to the next state
        async with state.proxy() as data:
            data["mode"] = mode[message.text]
            await Stats.next()
    else:
        await message.answer(c["t_BRStats"], reply_markup=start_markup)
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
            with open(f"assets/#not_found.png", "rb") as not_found:
                await message.answer_photo(not_found, c["t_Status404"], reply_markup=start_markup)
        elif resp["status"] == 403:  # It means user stats is private
            with open(f"assets/#private.png", "rb") as private:
                await message.answer_photo(private, c["t_Status403"], reply_markup=start_markup)
        elif resp["status"] == 200:  # It means everything should works fine
            generator = GenerateStats()  # Open #File.png then generate stats
            await generator.get_stats(message.text, data['mode'], resp["data"])
            with open(f"exports/{message.text}_{data['mode']}.png", "rb") as stats:
                await message.answer_photo(stats, c["t_Status200"].format(message.text), reply_markup=start_markup)
        elif resp["status"] == 429:  # It means you requested more than maximum allowed requests
            await message.answer(c["t_Status429"], reply_markup=start_markup)


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
