import os

import discord
from discord.ext import tasks


TOKEN = os.getenv("DISCORD_TOKEN", "F4K353C123TT0K3N")


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
