"""Module that contains main application logic."""

import os

from dotenv import load_dotenv

from logger.logger import logger
from services.discord_service import MyDiscordClient


def load_env() -> str:
    """
    Load ENV variables.
    :return: postgres_user, postgres_password, postgres_db
    """
    load_dotenv()
    discord_token = os.getenv("DISCORD_TOKEN")
    return discord_token


def main():
    """
    Main function.
    :return:
    """
    logger.info("Application started.")

    # Load env variables.
    discord_token = load_env()

    discord_client = MyDiscordClient()
    discord_client.run(discord_token)

    # # Setup database manager.
    # database_manager = DatabaseManager(
    #     url="sqlite+aiosqlite:///nepremicnine_database.sqlite"
    # )
    #
    # # Run the spider.
    # run_spider(database_manager=database_manager)

    logger.info("Application finished.")


if __name__ == "__main__":
    main()
