import sys
sys.path.insert(0, '/Users/alexanderkazakov/Documents/MyCode/sc2-mailmanich-test-bot/bot/')
from helpers import load_bot_name

import sc2

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SUPPLYDEPOT, BARRACKS, FACTORY, STARPORT, ENGINEERINGBAY, ARMORY, REFINERY
from sc2.constants import SCV, MARINE, SIEGETANK, MEDIVAC, VIKINGFIGHTER

# Opportunities
# - Build in a way that tanks can get out


class MyBot(sc2.BotAI):
    MAX_SIMULATANEOUS_SUPPLY_DEPOTS_BUILDING = 2
    SUPPLY_LEFT_TO_BUILD_DEPOT = 10
    EXPAND = 999999
    INITIAL_BUILD_ORDER = [SUPPLYDEPOT, BARRACKS, EXPAND, FACTORY, STARPORT]
    current_build_order_step = 0
    game_stage = 0
    last_iteration_with_order = 0
    NAME = load_bot_name()

    def dependencies_satisfied(self, what_to_build):
        if what_to_build == BARRACKS:
            return self.units(SUPPLYDEPOT).ready.exists
        if what_to_build == FACTORY:
            return self.units(BARRACKS).ready.exists
        if what_to_build == STARPORT:
            return self.units(FACTORY).ready.exists
        return True

    async def proceed_to_next_build_order_step(self):
        await self.chat_send(f"#{self.iteration} - Build phase step {self.current_build_order_step} complete!")
        self.current_build_order_step += 1
        if self.current_build_order_step == len(self.INITIAL_BUILD_ORDER):
            self.game_stage += 1
            await self.chat_send(f"#{self.iteration} - Build phase complete!")

    async def build_if_doesnt_exist(self, what_to_build):
        if self.can_afford(what_to_build) and self.dependencies_satisfied(what_to_build) and (not self.already_pending(what_to_build)) and (not self.units(what_to_build).exists):
            await self.build(what_to_build, near=self.units(COMMANDCENTER).first)
            await self.chat_send(f"#{self.iteration} - Building {what_to_build.name}")

    async def on_step(self, iteration):
        self.iteration = iteration
        await self.print_intel_to_chat(iteration)

        await self.distribute_workers()  # in sc2/bot_ai.p

        await self.build_workers()
        await self.train_army()
        await self.build_supply_depots()
        await self.build_refinery()

        if self.game_stage == 0:
            # Program Expansion
            # Fix it so that if it fails, there is a repeat

            what_to_build = self.INITIAL_BUILD_ORDER[self.current_build_order_step]
            if (what_to_build == self.EXPAND):
                if self.can_afford(COMMANDCENTER) and (not self.already_pending(COMMANDCENTER)) and (len(self.units(COMMANDCENTER)) < 2):
                    await self.expand_now()
                    await self.chat_send(f"#{self.iteration} - Build phase - Expanding")
                if (len(self.units(COMMANDCENTER)) >= 2):
                    await self.proceed_to_next_build_order_step()
            else:  # Normal structure building here
                await self.build_if_doesnt_exist(what_to_build)
                if self.units(what_to_build).exists:
                    await self.proceed_to_next_build_order_step()
        else:
            await self.expand()
            await self.build_more_barracks()

    async def build_workers(self):
        if self.units(SCV).amount < 70:
            for command_center in self.units(COMMANDCENTER).ready.noqueue:
                if self.can_afford(SCV):
                    await self.do(command_center.train(SCV))
                    await self.chat_send(f"#{self.iteration} - Training SCV")

    async def build_supply_depots(self):
        if self.supply_left < self.SUPPLY_LEFT_TO_BUILD_DEPOT and self.already_pending(SUPPLYDEPOT) < self.MAX_SIMULATANEOUS_SUPPLY_DEPOTS_BUILDING and self.supply_cap < 200:
            command_centers = self.units(COMMANDCENTER).ready
            if command_centers.exists:
                if self.can_afford(SUPPLYDEPOT):
                    await self.build(SUPPLYDEPOT, near=command_centers.first)
                    await self.chat_send(f"#{self.iteration} - Building Supply Depot")

    async def build_refinery(self):
        if (self.vespene < 100) and (not self.already_pending(REFINERY)) and self.can_afford(REFINERY):
            for command_center in self.units(COMMANDCENTER).ready:
                vaspenes = self.state.vespene_geyser.closer_than(10.0, command_center)
                for vaspene in vaspenes:
                    if (not self.units(REFINERY).closer_than(1.0, vaspene).exists):
                        worker = self.select_build_worker(vaspene.position)
                        if not (worker is None):
                            await self.do(worker.build(REFINERY, vaspene))
                            return True

    async def train_army(self):
        # Build 2 only if reactor?
        # Teach to hold if a structure is beng built
        if self.supply_left > 1:
            for barrack in self.units(BARRACKS).ready:
                if len(barrack.orders) < 2:
                    if self.can_afford(MARINE):
                        await self.do(barrack.train(MARINE))
                        await self.chat_send(f"#{self.iteration} - Training Marine")

            for factory in self.units(FACTORY).ready:
                if len(factory.orders) < 1:
                    if self.can_afford(SIEGETANK):
                        await self.do(factory.train(SIEGETANK))
                        await self.chat_send(f"#{self.iteration} - Producing a Tank")

            for starport in self.units(STARPORT).ready:
                if (len(starport.orders) < 1):
                    if self.units(MEDIVAC).amount < 5:
                        if self.can_afford(MEDIVAC):
                            await self.do(starport.train(MEDIVAC))
                            await self.chat_send(f"#{self.iteration} - Producing a Medivac")
                    else:
                        if self.can_afford(VIKINGFIGHTER):
                            await self.do(starport.train(VIKINGFIGHTER))
                            await self.chat_send(f"#{self.iteration} - Producing a Viking")

    async def expand(self):
        if self.units(COMMANDCENTER).amount < 4 and self.can_afford(COMMANDCENTER):
            await self.expand_now()
            await self.chat_send(f"#{self.iteration} - Expanding to new location")

    async def build_more_barracks(self):
        if self.supply_left > 10 and not self.already_pending(BARRACKS) and self.can_afford(BARRACKS) and self.units(BARRACKS).amount < self.units(COMMANDCENTER).amount*2:
            command_centers = self.units(COMMANDCENTER).ready
            if command_centers.exists:
                await self.build(BARRACKS, near=command_centers.random)
                await self.chat_send(f"#{self.iteration} - Building Barracks")

        await self.build_if_doesnt_exist(FACTORY)
        await self.build_if_doesnt_exist(STARPORT)
        await self.build_if_doesnt_exist(ENGINEERINGBAY)
        await self.build_if_doesnt_exist(ARMORY)


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

# ------------------------------------------------------

    async def print_intel_to_chat(self, iteration):
        if iteration == 0:
            await self.chat_send(f"I am a bot: {self.NAME}")

# ------------------------------------------------------
