from datetime import datetime, timedelta
from enum import Enum
import os
from typing import Tuple

import arrow
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks
import requests

TOKEN = os.getenv("DISCORD_TOKEN", "F4K353C123TT0K3N")


class Tracker:
    url: str
    time_format: str = "MMM DD, YYYY HH:mm A ZZZ"

    def parse(self, text):
        return "UNKNOWN", arrow.now()

    def get_em(self) -> Tuple[str, datetime]:
        soup = BeautifulSoup(requests.get(self.url).text, "html.parser")
        l, t = self.parse(soup)
        return l, arrow.get(t, self.time_format)


class TarkovPal(Tracker):
    url = "https://tarkovpal.com/api"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class GoonTracker(Tracker):
    url = "https://www.goon-tracker.com/"
    time_format = "YYYY-MM-DD HH:mm:ss"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class TarkovGoonTracker(Tracker):
    url = "https://www.tarkov-goon-tracker.com/"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class Brent(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.location = "unknown"

    async def setup_hook(self) -> None:
        self.poll_sightings.start()

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.Online, activity=discord.game("a video game")
        )
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    @tasks.loop(seconds=300)  # every 5 minutes
    async def poll_sightings(self):
        print("Fetch. Parse.")

    @poll_sightings.before_loop
    async def before_polling(self):
        await self.wait_until_ready()


client = Brent(intents=discord.Intents.default())
client.run(TOKEN)
