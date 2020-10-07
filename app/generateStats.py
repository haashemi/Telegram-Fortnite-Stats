
from PIL import Image, ImageFont, ImageDraw


class GenerateStats:
    """
    Class of everything that needed to make the Stats image
    """

    def __init__(self) -> None:
        """
        Open/Ready necessary things
        """
        self.stats = Image.open("assets/images/#file.png")
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
