from importlib import reload
import argparse
import sys
import asyncio

import json

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human

from bot import main_bot


def main():
    with open("botinfo.json") as f:
        info = json.load(f)

    race = Race[info["race"]]

    player_config = [Bot(race, main_bot.MyBot()), Computer(Race.Terran, Difficulty.Harder)]

    gen = sc2.main._host_game_iter(
            maps.get("(2)DreamcatcherLE"), player_config,
            realtime=True, step_time_limit=2.0, game_time_limit=(60*40))
#            save_replay_as="/Users/alexanderkazakov/Documents/MyCode/sc2-mailmanich-test-bot/test.SC2Replay")

    while True:
        r = next(gen)

        input("Press enter to reload ")

        reload(main_bot)
        player_config[0].ai = main_bot.MyBot()
        gen.send(player_config)


if __name__ == '__main__':
    main()
