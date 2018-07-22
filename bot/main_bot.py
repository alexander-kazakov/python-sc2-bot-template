import sys
sys.path.insert(0, '/Users/alexanderkazakov/Documents/MyCode/sc2-mailmanich-test-bot/bot/')
from helpers import load_bot_name

import sc2

from sc2.constants import COMMANDCENTER, SUPPLYDEPOT, BARRACKS, FACTORY, STARPORT, ENGINEERINGBAY, ARMORY, REFINERY, ORBITALCOMMAND
from sc2.constants import SCV, MARINE, SIEGETANK, MEDIVAC, VIKINGFIGHTER
from sc2.constants import UPGRADETOORBITAL_ORBITALCOMMAND, CALLDOWNMULE_CALLDOWNMULE

import math

# Opportunities
# - Build in a way that tanks can get out
# - Try building turrets
# - Get MULEs going
# - Use stimpack on marines when in attack and there is a medivac?

# Fix training with reactor

# Implement fast reload for easy testing

# Change so that it builds if no queue
#  for factory in self.units(FACTORY).ready.noqueue:

# Deploy MULEs
# # manage orbital energy and drop mules
# for oc in self.units(UnitTypeId.ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
#     mfs = self.state.mineral_field.closer_than(10, oc)
#     if mfs:
#         mf = max(mfs, key=lambda x:x.mineral_contents)
#         self.combinedActions.append(oc(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mf))
#
# Add Reactors
#         for sp in self.units(STARPORT).ready:
            # if sp.add_on_tag == 0:
            #     await self.do(sp.build(STARPORTTECHLAB))
#
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

    def time_str(self):
        minutes = math.floor(self.time / 60)
        seconds = math.floor(self.time % 60)
        return f"{minutes}:{str(seconds).zfill(2)}"

    async def log(self, message):
        await self.chat_send(f"#{self.time_str()} - {message}")

    def get_command_centers(self):
        return self.units.of_type([COMMANDCENTER, ORBITALCOMMAND])

    async def build_structure_try(self, structure):
        if self.can_afford(structure) and self.dependencies_satisfied(structure) and self.get_command_centers().ready.exists:
            await self.build(structure, near=self.get_command_centers().ready.first)
            await self.log(f"Building {structure.name}")

    async def train_unit_try(self, structure, unit):
        if self.can_afford(unit):
            await self.do(structure.train(unit))
            await self.log(f"Training {unit.name}")

    def add_on_name(self, structure):
        if structure.add_on_tag != 0:
            return self.units.find_by_tag(structure.add_on_tag).name
        else:
            return "None"


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
                if (len(self.get_command_centers()) >= 2):
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
            for command_center in self.get_command_centers().ready.noqueue:
                await self.train_unit_try(command_center, SCV)

        for oc in self.units(ORBITALCOMMAND).filter(lambda x: x.energy >= 50):
            mfs = self.state.mineral_field.closer_than(10, oc)
            if mfs:
                mf = max(mfs, key=lambda x: x.mineral_contents)
                self.do(oc(CALLDOWNMULE_CALLDOWNMULE, mf))

    async def build_supply_depots(self):
        if (self.supply_left < self.SUPPLY_LEFT_TO_BUILD_DEPOT and
            self.already_pending(SUPPLYDEPOT) < self.MAX_SIMULATANEOUS_SUPPLY_DEPOTS_BUILDING and
            self.supply_cap < 200):
                await self.build_structure_try(SUPPLYDEPOT)

    async def build_refinery(self):
        if ((self.vespene < 100) and (not self.already_pending(REFINERY)) and
            self.can_afford(REFINERY) and self.units(REFINERY).amount < math.floor(self.time/60)*2):
            for command_center in self.get_command_centers().ready:
                vaspenes = self.state.vespene_geyser.closer_than(10.0, command_center)
                for vaspene in vaspenes:
                    if (not self.units(REFINERY).closer_than(1.0, vaspene).exists):
                        worker = self.select_build_worker(vaspene.position)
                        if not (worker is None):
                            await self.do(worker.build(REFINERY, vaspene))
                            return True

    async def train_army(self):
        if self.supply_left > 1:
            for barrack in self.units(BARRACKS).ready:
                if ((len(barrack.orders) < 1) or
                    (self.add_on_name(barrack) == "BarracksReactor" and len(barrack.orders) < 2)):
                    await self.train_unit_try(barrack, MARINE)

            for factory in self.units(FACTORY).ready.noqueue:
                if (self.add_on_name(factory) == "FactoryTechLab"):
                    await self.train_unit_try(factory, SIEGETANK)

            for starport in self.units(STARPORT).ready.noqueue:
                if ((len(starport.orders) < 1) or
                    (self.add_on_name(starport) == "StarportReactor" and len(starport.orders) < 2)):
                    if self.units(MEDIVAC).amount < self.MAX_MEDIVACS:
                        await self.train_unit_try(starport, MEDIVAC)
                    else:
                        await self.train_unit_try(starport, VIKINGFIGHTER)

    async def expand(self):
        if (self.get_command_centers().amount < 4 and
                    self.can_afford(COMMANDCENTER) and
                    self.units(SCV).amount > self.get_command_centers().amount*16):
            await self.expand_now()
            await self.log("Expanding to new location")

    async def build_structures(self):
        for cc in self.units(COMMANDCENTER).idle:
                self.do(cc(UPGRADETOORBITAL_ORBITALCOMMAND))

        await self.build_more_barracks()

        await self.build_if_doesnt_exist(FACTORY)
        await self.build_if_doesnt_exist(STARPORT)

        if self.time > 180:
            await self.build_if_doesnt_exist(ENGINEERINGBAY)
            await self.build_if_doesnt_exist(ARMORY)

    async def build_more_barracks(self):
        if (self.supply_left > 5 and not self.already_pending(BARRACKS) and
                self.units(BARRACKS).amount < self.units(COMMANDCENTER).amount*2):
            await self.build_structure_try(BARRACKS)
