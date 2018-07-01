import json

import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer, Human

from bot import MyBot

def main():
    with open("botinfo.json") as f:
        info = json.load(f)

    race = Race[info["race"]]

    run_game(maps.get("(2)DreamcatcherLE"), [
        #Human(Race.Terran),
        Bot(race, MyBot())
        , Computer(Race.Terran, Difficulty.Easy)
    ], realtime=False, step_time_limit=2.0, game_time_limit=(60*40), save_replay_as="/Users/alexanderkazakov/Documents/MyCode/sc2-mailmanich-test-bot/test.SC2Replay")

if __name__ == '__main__':
    main()
