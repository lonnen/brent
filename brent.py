from datetime import datetime
import json
import logging
import os
from typing import Tuple

import arrow
from bs4 import BeautifulSoup
import discord
from discord.ext import tasks
import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("DISCORD_TOKEN", "F4K353C123TT0K3N")


class Tracker:
    name: str = "Tracker"
    time_format: str = "MMM DD, YYYY HH:mm A ZZZ"
    url: str

    default_location: str = "UNKOWN"
    default_time: str = arrow.Arrow(1970, 1, 1, 0, 0, 0)

    last_successful_check: arrow.Arrow
    last_location_seen: str = default_location
    last_time_seen: str = default_time

    def parse(self, text):
        return self.default_location, self.default_time

    def get_em(self) -> Tuple[str, datetime]:
        r = requests.get(self.url)
        if not r.ok:
            logger.error(f"Error while fetching {self.name} - {r.status_code}")
            return self.default_location, self.default_time
        soup = BeautifulSoup(r.text, "html.parser")
        try:
            l, t = self.parse(soup)
        except AttributeError as ae:
            logger.error(f"Error while fetching {self.name} - {ae}")
            return self.default_location, self.default_time
        self.last_successful_check = arrow.now()
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
        return [x.text for x in text.find("tbody").tr.contents[1:4:2]]


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
            status=discord.Status.idle,
            activity=discord.CustomActivity("Raid Loading..."),
        )
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    @tasks.loop(seconds=300)  # every 5 minutes
    async def poll_sightings(self):
        successes = 0
        now = arrow.now()
        for tracker in self.trackers:
            loc, sighting = tracker.get_em()
            if loc == Tracker.default_location:
                continue
            else:
                successes += 1
            if sighting > self.last_sighting:
                self.location = loc
                self.last_sighting = sighting
                self.source = tracker.name

        dt = self.last_sighting.humanize(now, only_distance=True)
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.CustomActivity(
                f"{self.location} | {dt} ago ({self.source})"
            ),
        )
        time_to_poll = (arrow.now() - now).seconds
        logger.info(
            f"Poll: {successes} of {len(self.trackers)} in {time_to_poll} seconds"
        )

    @poll_sightings.before_loop
    async def before_polling(self):
        await self.wait_until_ready()


if __name__ == "__main__":
    client = Brent(intents=discord.Intents.default())
    client.run(TOKEN)
