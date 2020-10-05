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
    def __init__(self) -> None:
        self.stats = Image.open("assets/#file.png")
        self.draw = ImageDraw.Draw(self.stats)
        self.font = ImageFont.truetype(
            r"assets/fonts/BurbankBigCondensed-Black.ttf", 60)

    async def draw_on(self, position: tuple, text, color: tuple = None) -> None:
        color = color if color is not None else (255, 255, 255)
        self.draw.text(position, str(text), color, self.font)

    async def get_stats(self, username, mode: str, data: dict) -> None:
        await self.draw_on((140, 155), data["account"]["name"])
        await self.draw_on((785, 155),
                           str(data["battlePass"]["level"]) + "." + str(data["battlePass"]["progress"]))
        await self.draw_on((140, 400), data["stats"]["all"][mode]["wins"])

        if mode == "overall" or mode == "solo":
            await self.draw_on((590, 310), "10", (0, 228, 255))
            await self.draw_on((535, 400), data["stats"]["all"][mode]["top10"])
            await self.draw_on((990, 310), "25", (0, 228, 255))
            await self.draw_on((930, 400), data["stats"]["all"][mode]["top25"])
        elif mode == "duo":
            await self.draw_on((590, 310), "5", (0, 228, 255))
            await self.draw_on((535, 400), data["stats"]["all"][mode]["top5"])
            await self.draw_on((990, 310), "12", (0, 228, 255))
            await self.draw_on((930, 400), data["stats"]["all"][mode]["top12"])
        elif mode == "squad":
            await self.draw_on((590, 310), "3", (0, 228, 255))
            await self.draw_on((535, 400), data["stats"]["all"][mode]["top3"])
            await self.draw_on((990, 310), "5", (0, 228, 255))
            await self.draw_on((930, 400), data["stats"]["all"][mode]["top6"])

        await self.draw_on((140, 650), data["stats"]["all"][mode]["kills"])
        await self.draw_on((535, 650), data["stats"]["all"][mode]["killsPerMatch"])
        await self.draw_on((930, 650), data["stats"]["all"][mode]["kd"])
        await self.draw_on((140, 905), data["stats"]["all"][mode]["matches"])
        await self.draw_on((930, 905), data["stats"]["all"][mode]["winRate"])
        await self.draw_on((140, 1140), data["stats"]["all"][mode]["minutesPlayed"])
        await self.draw_on((785, 1140), mode.upper())

        self.stats.save(f"exports/{username}_{mode}.png")


# +------------------+
# |Main Menu commands|
# +------------------+
start_btns = [
    [types.KeyboardButton("📊 Battle Royale Stats"),
     types.KeyboardButton("⁉️About this bot")
     ]
]
start_markup = types.ReplyKeyboardMarkup(
    keyboard=start_btns, resize_keyboard=True)


@dp.message_handler(commands="start")
async def start_menu(message: types.Message):
    await message.answer(c["t_Start"], reply_markup=start_markup)


@dp.message_handler(lambda message: message.text == '↩️ Back to home', state="*")
async def back_to_home(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    await message.answer(c["t_BackToHome"], reply_markup=start_markup)


# +-----------------+
# | Start Menu BTNS |
# +-----------------+
class Stats(StatesGroup):
    mode = State()
    username = State()


@dp.message_handler(lambda message: message.text == "📊 Battle Royale Stats")
async def stats_menu(message: types.Message):
    modes_btns = [
        [types.KeyboardButton("☑️ Overall"), types.KeyboardButton("🔴 Solo")],
        [types.KeyboardButton("🔵 Duos"), types.KeyboardButton("🟢 Squads")]
    ]
    modes_markup = types.ReplyKeyboardMarkup(
        keyboard=modes_btns, resize_keyboard=True)
    await message.answer(c["t_BRStats"], reply_markup=modes_markup)
    await Stats.mode.set()


@dp.message_handler(lambda message: message.text == "⁉️About this bot")
async def about_bot(message: types.Message):
    await message.answer(c["t_AboutBot"])


# +-----------------+
# | Start Menu BTNS |
# +-----------------+
@dp.message_handler(state=Stats.mode)
async def mode_state(message: types.Message, state: FSMContext):
    mode = {
        "☑️ Overall": "overall",
        "🔴 Solo": "solo",
        "🔵 Duos": "duo",
        "🟢 Squads": "squad"
    }
    if message.text in mode:
        await message.answer(
            c["t_SendUsername"],
            reply_markup=types.ReplyKeyboardMarkup(
                keyboard=[[types.KeyboardButton("↩️ Back to home")]],
                resize_keyboard=True)
        )
        async with state.proxy() as data:
            data["mode"] = mode[message.text]
            await Stats.next()
    else:
        await message.answer(c["t_BRStats"], reply_markup=start_markup)
        await state.finish()


@dp.message_handler(state=Stats.username)
async def username_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        account_params = {"name": str(
            message.text), "accountType": "epic", "timeWindow": "lifetime"}
        resp = await get_url(account_params)

        if resp["status"] == 404:
            await message.answer(c["t_Status404"], reply_markup=start_markup)
        elif resp["status"] == 403:
            await message.answer(c["t_Status403"], reply_markup=start_markup)
        elif resp["status"] == 200:
            generator = GenerateStats()
            await generator.get_stats(message.text, data['mode'], resp["data"])
            with open(f"exports/{message.text}_{data['mode']}.png", "rb") as stats:
                await message.answer_photo(stats, c["t_Status200"].format(message.text), reply_markup=start_markup)
        else:
            await message.answer(c["t_StatusERR"], reply_markup=start_markup)
        await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
