import aiohttp
from PIL import Image, ImageFont, ImageDraw

session = aiohttp.ClientSession()
fn_stats_url = "https://fortnite-api.com/v1/stats/br/v2"


async def get_url(url: str, params: dict) -> dict:
    """
    Get url then return json encoded of that

    :param url: url of the website
    :param params: pass parameters of the url
    :return: json encoded dictionary
    """
    async with session.get(url=url, params=params) as resp:
        print(resp.status)
        print(await resp.json())


async def get_stats(username: str, mode: str):
    player = username
    if player.isspace():
        player.strip()
        player.replace(" ", "%20")
    try:
        account_params = {"name": username, "accountType": "epic", "timeWindow": "lifetime"}
        resp = await get_url(fn_stats_url, account_params)

        status = {'status': str(url["status"])}
        if str(url["status"]) == "404" or str(url["status"]) == "403":
            return status
        elif url["data"]["battlePass"] is None:
            status = {'status': "404"}
            return status
        elif str(url["status"]) == "200":
            img = Image.open("assets/#file.png")
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype(r"assets/fonts/BurbankBigCondensed-Black.ttf", 60)

            name = url["data"]["account"]["name"]
            draw.text((140, 155), name, (255, 255, 255), font=font)

            level = str(url["data"]["battlePass"]["level"]) + "." + str(url["data"]["battlePass"]["progress"])
            draw.text((785, 155), level, (255, 255, 255), font=font)

            wins = str(url["data"]["stats"]["all"][mode]["wins"])
            draw.text((140, 400), wins, (255, 255, 255), font=font)

            if mode == "overall" or mode == "solo":
                draw.text((590, 310), "10", (0, 228, 255), font=font)
                draw.text((990, 310), "25", (0, 228, 255), font=font)

                top10 = str(url["data"]["stats"]["all"][mode]["top10"])
                top25 = str(url["data"]["stats"]["all"][mode]["top25"])
                draw.text((535, 400), top10, (255, 255, 255), font=font)
                draw.text((930, 400), top25, (255, 255, 255), font=font)
            elif mode == "duo":
                draw.text((590, 310), "5", (0, 228, 255), font=font)
                draw.text((990, 310), "12", (0, 228, 255), font=font)

                top5 = str(url["data"]["stats"]["all"][mode]["top5"])
                top12 = str(url["data"]["stats"]["all"][mode]["top12"])
                draw.text((535, 400), top5, (255, 255, 255), font=font)
                draw.text((930, 400), top12, (255, 255, 255), font=font)
            elif mode == "squad":
                draw.text((590, 310), "3", (0, 228, 255), font=font)
                draw.text((990, 310), "5", (0, 228, 255), font=font)

                top3 = str(url["data"]["stats"]["all"][mode]["top3"])
                top6 = str(url["data"]["stats"]["all"][mode]["top6"])
                draw.text((535, 400), top3, (255, 255, 255), font=font)
                draw.text((930, 400), top6, (255, 255, 255), font=font)

            kills = str(url["data"]["stats"]["all"][mode]["kills"])
            draw.text((140, 650), kills, (255, 255, 255), font=font)

            kills_permatch = str(url["data"]["stats"]["all"][mode]["killsPerMatch"])
            draw.text((535, 650), kills_permatch, (255, 255, 255), font=font)

            kd = str(url["data"]["stats"]["all"][mode]["kd"])
            draw.text((930, 650), kd, (255, 255, 255), font=font)

            matches = str(url["data"]["stats"]["all"][mode]["matches"])
            draw.text((140, 905), matches, (255, 255, 255), font=font)

            winRate = str(url["data"]["stats"]["all"][mode]["winRate"])
            draw.text((930, 905), winRate, (255, 255, 255), font=font)

            minutesPlayed = str(url["data"]["stats"]["all"][mode]["minutesPlayed"])
            draw.text((140, 1140), minutesPlayed, (255, 255, 255), font=font)
            draw.text((785, 1140), mode, (255, 255, 255), font=font)

            return img
    except:
        return {'status': "404"}
