import json
from pathlib import Path

import sc2

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR

class MyBot(sc2.BotAI):
    with open(Path(__file__).parent / "../botinfo.json") as f:
        NAME = json.load(f)["name"]


    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send(f"Name: {self.NAME}")


        await self.log_info(iteration, iteration)

        if len(self.known_enemy_units) > 0:
            await self.attack(iteration)
        else:
            await self.distribute_workers()  # in sc2/bot_ai.p

        await self.build_workers()
        await self.build_assimilator()
        await self.build_pylons()


    async def build_workers(self):
        for nexus in self.units(NEXUS).ready.noqueue:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    await self.build(PYLON, near=nexuses.first)


    async def build_assimilator(self):
        for nexus in self.units(NEXUS).ready:
            vaspenes = self.state.vespene_geyser.closer_than(10.0, nexus)
            for vaspene in vaspenes:
                if (not self.units(ASSIMILATOR).closer_than(1.0, vaspene).exists) and self.can_afford(ASSIMILATOR):
                    worker = self.select_build_worker(vaspene.position)
                    if not (worker is None):
                        await self.do(worker.build(ASSIMILATOR, vaspene))

    async def attack(self, iteration):
        self.log_info(iteration, len(self.known_enemy_units))
        if len(self.known_enemy_units) > 0:
            for s in self.units(PROBE).idle:
                await self.do(s.attack(self.known_enemy_units.first))

    async def log_info(self, iteration, info):
        if (iteration % 100 == 0):
            await self.chat_send(f"Info: {info}")
