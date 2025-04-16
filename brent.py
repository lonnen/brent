from datetime import datetime, timedelta
from enum import Enum
import json
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
        return "UNKNOWN", arrow.Arrow(1970, 1, 1, 0, 0, 0)

    def get_em(self) -> Tuple[str, datetime]:
        r = requests.get(self.url)
        if not r.ok:
            print(f"Error while fetching {self.name} - {r.status_code}")
            return "UNKNOWN", arrow.Arrow(1970, 1, 1, 0, 0, 0)
        soup = BeautifulSoup(r.text, "html.parser")
        try:
            l, t = self.parse(soup)
        except AttributeError as ae:
            print(f"Error while fetching {self.name} - {ae}")
            return "UNKNOWN", arrow.Arrow(1970, 1, 1, 0, 0, 0)
        return l, arrow.get(t, self.time_format)


class TarkovPal(Tracker):
    name = "Tarkov Pal"
    url = "https://tarkovpal.com/api"
    time_format = "MMMM D, YYYY, H:m A"

    def parse(self, text) -> Tuple[str, str]:
        j = json.loads(text.string)
        return j["Current Map"][0], j["Time"][0]


class GoonTracker(Tracker):
    name = "Goon Tracker"
    url = "https://www.goon-tracker.com/"
    time_format = "YYYY-MM-DD HH:mm:ss"

    def parse(self, text):
        return [x.text for x in text.find('tbody').tr.contents[1:4:2]]


class TarkovGoonTracker(Tracker):
    name = "Tarkov Goon Tracker"
    url = "https://www.tarkov-goon-tracker.com/"

    def parse(self, text):
        return [x.text for x in text.find(id="trackings").tbody.tr.contents[:2]]


class Brent(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.trackers: Tracker = [TarkovPal(), GoonTracker(), TarkovGoonTracker()]

        self.location = "UNKNOWN"
        self.last_sighting = arrow.Arrow(1970, 1, 1, 0, 0, 0)
        self.source = "UNKNOWN"

    async def setup_hook(self) -> None:
        self.poll_sightings.start()

    async def on_ready(self):
        await self.change_presence(
            status=discord.Status.idle, activity=discord.Game("Raid Loading...")
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
            activity=discord.Game(f"{self.location} {dt} ago ({self.source})"),
        )

    @poll_sightings.before_loop
    async def before_polling(self):
        await self.wait_until_ready()


client = Brent(intents=discord.Intents.default())
client.run(TOKEN)
