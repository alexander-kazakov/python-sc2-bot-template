import sys
sys.path.insert(0, '/Users/alexanderkazakov/Documents/MyCode/sc2-mailmanich-test-bot/bot/')
from helpers import load_bot_name

import sc2

from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import COMMANDCENTER, SUPPLYDEPOT, BARRACKS, FACTORY, STARPORT, ENGINEERINGBAY, ARMORY, REFINERY
from sc2.constants import SCV, MARINE, SIEGETANK, MEDIVAC, VIKINGFIGHTER

import math

# Opportunities
# - Build in a way that tanks can get out
# - Try building turrets
# - Get MULEs going
# - Use stimpack on marines when in attack and there is a medivac?

# Change so that it builds if no queue
#  for factory in self.units(FACTORY).ready.noqueue:

# Upgrading to orbital command
# if self.units(UnitTypeId.BARRACKS).ready.exists and self.can_afford(UnitTypeId.BARRACKS): # we dont check if we can afford because the price for morphing units was/is bugged - doesn't work with "await self.do()"
#            for cc in self.units(COMMANDCENTER).idle: # .idle filters idle command centers
#                self.combinedActions.append(cc(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND))

# Deploy MULEs
# # manage orbital energy and drop mules
# for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
#     mfs = self.state.mineral_field.closer_than(10, oc)
#     if mfs:
#         mf = max(mfs, key=lambda x:x.mineral_contents)
#         self.combinedActions.append(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))
#

# HOW TO DEFINE BUILDING LOCATION
#                         p = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
#                        await self.build(FACTORY, near=p)

class MyBot(sc2.BotAI):
    MAX_SIMULATANEOUS_SUPPLY_DEPOTS_BUILDING = 2
    SUPPLY_LEFT_TO_BUILD_DEPOT = 10
    EXPAND = 999999
    INITIAL_BUILD_ORDER = [SUPPLYDEPOT, BARRACKS, EXPAND, FACTORY, STARPORT]
    current_build_order_step = 0
    game_stage = 0
    last_iteration_with_order = 0
    MAX_MEDIVACS = 3
    NAME = load_bot_name()

# -----  HELPER FUNCTIONS ----------------------------------------

    def dependencies_satisfied(self, what_to_build):
        if what_to_build == BARRACKS:
            return self.units(SUPPLYDEPOT).ready.exists
        elif what_to_build == FACTORY:
            return self.units(BARRACKS).ready.exists
        elif what_to_build == STARPORT:
            return self.units(FACTORY).ready.exists
        else:
            return True

    async def proceed_to_next_build_order_step(self):
        await self.log(f"Build phase step {self.current_build_order_step} complete!")
        self.current_build_order_step += 1
        if self.current_build_order_step == len(self.INITIAL_BUILD_ORDER):
            self.game_stage += 1
            await self.log("Build phase complete!")

    async def build_if_doesnt_exist(self, what_to_build):
        if (not self.already_pending(what_to_build)) and (not self.units(what_to_build).exists):
            await self.build_structure_try(what_to_build)

    async def initialize_step(self, iteration):
        if iteration == 0:
            await self.chat_send(f"I am a bot: {self.NAME}")

        self.iteration = iteration
        self.time = (self.state.game_loop/22.4)

    def time_str(self):
        minutes = math.floor(self.time / 60)
        seconds = math.floor(self.time % 60)
        return f"{minutes}:{str(seconds).zfill(2)}"

    async def log(self, message):
        await self.chat_send(f"#{self.time_str()} - {message}")

    async def build_structure_try(self, structure):
        if self.can_afford(structure) and self.dependencies_satisfied(structure) and self.units(COMMANDCENTER).ready.exists:
            await self.build(structure, near=self.units(COMMANDCENTER).ready.first)
            await self.log(f"Building {structure.name}")

    async def train_unit_try(self, structure, unit):
        if self.can_afford(unit):
            await self.do(structure.train(unit))
            await self.log(f"Training {unit.name}")


# -----  MAIN LOOP ----------------------------------------

    async def on_step(self, iteration):
        await self.initialize_step(iteration)

        await self.distribute_workers()  # in sc2/bot_ai.p

        if self.game_stage == 0:
            # Program Expansion
            # Fix it so that if it fails, there is a repeat

            what_to_build = self.INITIAL_BUILD_ORDER[self.current_build_order_step]
            if (what_to_build == self.EXPAND):
                if self.can_afford(COMMANDCENTER) and (not self.already_pending(COMMANDCENTER)) and (len(self.units(COMMANDCENTER)) < 2):
                    await self.expand_now()
                    await self.log("Build phase - Expanding")
                if (len(self.units(COMMANDCENTER)) >= 2):
                    await self.proceed_to_next_build_order_step()
            else:  # Normal structure building here
                await self.build_if_doesnt_exist(what_to_build)
                if self.units(what_to_build).exists:
                    await self.proceed_to_next_build_order_step()
        else:
            await self.expand()
            await self.build_structures()

        await self.build_workers()
        await self.build_supply_depots()
        await self.train_army()
        await self.build_refinery()

# -----  GAME MANAGEMENT ----------------------------------------

    async def build_workers(self):
        if self.units(SCV).amount < 70:
            for command_center in self.units(COMMANDCENTER).ready.noqueue:
                await self.train_unit_try(command_center, SCV)

    async def build_supply_depots(self):
        if (self.supply_left < self.SUPPLY_LEFT_TO_BUILD_DEPOT and
            self.already_pending(SUPPLYDEPOT) < self.MAX_SIMULATANEOUS_SUPPLY_DEPOTS_BUILDING and
            self.supply_cap < 200):
                await self.build_structure_try(SUPPLYDEPOT)

    async def build_refinery(self):
        if ((self.vespene < 100) and (not self.already_pending(REFINERY)) and
            self.can_afford(REFINERY) and self.units(REFINERY).amount < math.floor(self.time/60)*2):
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
                    await self.train_unit_try(barrack, MARINE)

            for factory in self.units(FACTORY).ready:
                if len(factory.orders) < 1:
                    await self.train_unit_try(factory, SIEGETANK)

            for starport in self.units(STARPORT).ready:
                if (len(starport.orders) < 1):
                    if self.units(MEDIVAC).amount < self.MAX_MEDIVACS:
                        await self.train_unit_try(starport, MEDIVAC)
                    else:
                        await self.train_unit_try(starport, VIKINGFIGHTER)

    async def expand(self):
        if (self.units(COMMANDCENTER).amount < 4 and
                    self.can_afford(COMMANDCENTER) and
                    self.units(SCV).amount > self.units(COMMANDCENTER).amount*16):
            await self.expand_now()
            await self.log("Expanding to new location")

    async def build_structures(self):
        await self.build_more_barracks()

        await self.build_if_doesnt_exist(FACTORY)
        await self.build_if_doesnt_exist(STARPORT)
        await self.build_if_doesnt_exist(ENGINEERINGBAY)
#        await self.build_if_doesnt_exist(ARMORY)

    async def build_more_barracks(self):
        if (self.supply_left > 5 and not self.already_pending(BARRACKS) and
                self.units(BARRACKS).amount < self.units(COMMANDCENTER).amount*2):
            await self.build_structure_try(BARRACKS)
