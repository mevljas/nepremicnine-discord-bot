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
        """
        Called when the bot is ready.
        :return:
        """
        logging.debug("""Logged in as %s (ID: %s)""", self.user, self.user.id)
        logging.debug("------")

    @tasks.loop(hours=1)  # task runs every 1 hour
    async def my_background_task(self):
        """
        Background task that runs every 1 hour.
        :return:
        """
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
            title, image_url, description, prices, size, year, floor, url = listing
            embed = discord.Embed(
                title=title,
                url=url,
                description=description,
                color=discord.Color.blue(),
            )
            embed.set_image(url=image_url)
            embed.add_field(
                name="**Cena**",
                value=f"{prices[0]:.2f} €",
                inline=True,
            )
            embed.add_field(
                name="**Velikost**",
                value=f"{size:.2f} m²",
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

            if len(prices) > 1:
                embed.add_field(
                    name="**Prejšnje cene**",
                    value=", ".join(f"{price:.2f} €" for price in prices[1:]),
                    inline=False,
                )

            await channel.send(embed=embed)

    @my_background_task.before_loop
    async def before_my_task(self):
        """
        Wait until the bot is ready.
        :return:
        """
        await self.wait_until_ready()  # wait until the bot logs in
