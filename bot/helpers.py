import json
from pathlib import Path


def load_bot_name():
    with open(Path(__file__).parent / "../botinfo.json") as f:
        return json.load(f)["name"]
