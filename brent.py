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
    name: str = "Tracker"
    time_format: str = "MMM DD, YYYY HH:mm A ZZZ"
    url: str

    def parse(self, text):
        return "UNKNOWN", arrow.now()

    def get_em(self) -> Tuple[str, datetime]:
        soup = BeautifulSoup(requests.get(self.url).text, "html.parser")
        l, t = self.parse(soup)
        return l, arrow.get(t, self.time_format)


class TarkovPal(Tracker):
    name = "Tarkov Pal"
    url = "https://tarkovpal.com/api"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class GoonTracker(Tracker):
    name = "Goon Tracker"
    url = "https://www.goon-tracker.com/"
    time_format = "YYYY-MM-DD HH:mm:ss"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class TarkovGoonTracker(Tracker):
    name = "Tarkov Goon Tracker"
    url = "https://www.tarkov-goon-tracker.com/"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class Brent(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.trackers: Tracker = [TarkovPal, GoonTracker, TarkovGoonTracker]

        self.location = "UNKNOWN"
        self.last_sighting = arrow.now()
        self.source = "UNKNOWN"

    async def setup_hook(self) -> None:
        self.poll_sightings.start()

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.idle, activity=discord.game("Raid Loading...")
        )
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    @tasks.loop(seconds=300)  # every 5 minutes
    async def poll_sightings(self):
        now = arrow.now()
        for tracker in self.trackers:
            loc, sighting = tracker.get_em()
            if sighting > self.last_sighting:
                self.location = loc
                self.last_sighting = sighting
                self.source = tracker.name

        dt = arrow.humanize(
            now - self.last_sighting, only_distance=True, granularity=["hour", "minute"]
        )
        self.change_presence(
            status=discord.Status.online,
            activity=discord.game(f"{self.location} {dt} ago ({self.source})"),
        )

    @poll_sightings.before_loop
    async def before_polling(self):
        await self.wait_until_ready()


client = Brent(intents=discord.Intents.default())
client.run(TOKEN)
