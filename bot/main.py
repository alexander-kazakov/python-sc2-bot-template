from .helpers import load_bot_name

import sc2

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON, ASSIMILATOR


class MyBot(sc2.BotAI):
    LOGGING_FREQUENCY = 50
    NAME = load_bot_name()

    async def on_step(self, iteration):
        await self.print_intel_to_chat(iteration)

        await self.distribute_workers()  # in sc2/bot_ai.p

    #     await self.build_workers()
    #
    # async def build_workers(self):
    #     for nexus in self.units(NEXUS).ready.noqueue:
    #         if self.can_afford(probe):
    #             await self.do(nexus.train(PROBE))
    #
    # async def build_pylons(self):
    #     if self.supply_left < 5 and not self.already_pending(PYLON):
    #         nexuses = self.units(NEXUS).ready
    #         if nexuses.exists:
    #             if self.can_afford(PYLON):
    #                 await self.build(PYLON, near=nexuses.first)
    #
    #
    # async def build_assimilator(self):
    #     for nexus in self.units(NEXUS).ready:
    #         vaspenes = self.state.vespene_geyser.closer_than(10.0, nexus)
    #         for vaspene in vaspenes:
    #             if (not self.units(ASSIMILATOR).closer_than(1.0, vaspene)
    #                               .exists) and self.can_afford(ASSIMILATOR):
    #                 worker = self.select_build_worker(vaspene.position)
    #                 if not (worker is None):
    #                     await self.do(worker.build(ASSIMILATOR, vaspene))
    #
    # async def attack(self, iteration):
    #     self.log_info(iteration, "Attacking!")
    #     if (self.known_enemy_units.amount > 0):
    #         for s in self.units(PROBE):
    #             await self.do(s.attack(self.known_enemy_units.random))
    #
    # async def expand(self):
    #     if self.units(NEXUS).amount < 3 and self.can_afford(NEXUS):
    #         await self.expand_now()

# ------------------------------------------------------

    async def print_intel_to_chat(self, iteration):
        if iteration == 0:
            await self.chat_send(f"I am a bot: {self.NAME}")

        if (iteration % self.LOGGING_FREQUENCY == 0):
            await self.chat_send(f"Iteration: {iteration}")
            await self.chat_send(f"Enemies detected: \
                                    {self.known_enemy_units.amount}")

# ------------------------------------------------------
