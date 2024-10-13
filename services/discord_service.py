"""
Module that contains discord bot logic.
"""

import logging

import discord
from discord.ext import tasks

from database.database_manager import DatabaseManager
from spider.spider import run_spider


class MyDiscordClient(discord.Client):
    """
    Nepremicnine.si Discord bot client.
    """

    def __init__(self):
        super().__init__(intents=discord.Intents.default())

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.my_background_task.start()

    async def on_ready(self):
        logging.debug("""Logged in as %s (ID: %s)""", self.user, self.user.id)
        logging.debug("------")

    @tasks.loop(hours=1)  # task runs every 1 hour
    async def my_background_task(self):
        channel = self.get_channel(1294990979475963994)  # channel ID goes here
        # await channel.send("Hello, world!")

        # Setup database manager.
        database_manager = DatabaseManager(
            url="sqlite+aiosqlite:///nepremicnine_database.sqlite"
        )

        # Run the spider.
        listings = await run_spider(database_manager=database_manager)

        await channel.send(f"Found {len(listings)} new listings.")

        for listing in listings:
            title, image_url, description, price, size, year, floor, url = listing
            embed = discord.Embed(
                title=title,
                url=url,
                description=description,
                color=discord.Color.blue(),
            )
            embed.set_image(url=image_url)
            embed.add_field(
                name="**Cena**",
                value="{:.2f} €".format(price),
                inline=True,
            )
            embed.add_field(
                name="**Velikost**",
                value="{:.2f} m²".format(size),
                inline=True,
            )
            embed.add_field(
                name="**Zgrajeno leta**",
                value=year,
                inline=True,
            )
            embed.add_field(
                name="**Nadstropje**",
                value=floor,
                inline=True,
            )

            await channel.send(embed=embed)

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in
