import asyncio
import logging
import time

import discord

from bot_variables import BotVariables
import get_ai_response as ai


bot_vars: BotVariables
LOGGER = logging.getLogger(__name__)


async def save_on_disk_task():
    while True:
        await asyncio.sleep(60.0)

        async with asyncio.Lock():
            try:
                bot_vars.write_to_file("data/bot_vars.csv")
                LOGGER.info("Saved bot_vars to a file")
            except Exception as e:
                LOGGER.error(f"Exception while writing to a file: {e}")


async def presence_task():
    while True:
        try:
            presence: str = f"Я гнию изнутри..."
            activity = discord.Activity(type=discord.ActivityType.playing, name=presence)
            await bot_vars.client.change_presence(activity=activity)
        except Exception as e:
            LOGGER.error(f"Exception while changing presence: {e}")

        await asyncio.sleep(10.0)