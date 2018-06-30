import json
from pathlib import Path

import sc2

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer


class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")

        # what to do every step
        await self.distribute_workers()  # in sc2/bot_ai.py
