import json
from pathlib import Path

import requests
from appcfg import get_config
from bs4 import BeautifulSoup

config = get_config(__name__)

TARGET_GAME_ID = config["target_game_id"]
GAME_STATE_FILE = "data/game_state.json"
WEBHOOK_URL = config["slack_webhook_url"]

players = config["players"]

def extract_json(s):
    prefix = "window.initialGames ="
    suffix = ";"

    s = s.strip()

    # Check and remove the prefix
    if s.startswith(prefix):
        s = s[len(prefix):]

    # Check and remove the suffix
    if s.endswith(suffix):
        s = s[:-len(suffix)]

    # Trim whitespace
    return s.strip()

last_game_state = {
    "last_move_at": None,
    "current_player_name": None,
}

file_path = Path(__file__).parent / GAME_STATE_FILE
if not file_path.exists():
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(last_game_state, indent=4, sort_keys=True))

with open(file_path, 'r') as raw_state:
    last_game_state = json.load(raw_state)

r = requests.get("https://www.playimperial.club/")
if r.status_code == 200:
    soup = BeautifulSoup(r.text, 'html.parser')

    text = None
    scripts = soup.find_all('script')
    for script in scripts:
        if "window.initialGames" in script.text:
            text = extract_json(script.text)
            break
    if text:
        games = json.loads(text)
        for game in games:
            if game["id"] == TARGET_GAME_ID:

                game_state = {
                    "last_move_at": game["last_move_at"],
                    "current_player_name": game["current_player_name"],
                }

                if game_state["last_move_at"] != last_game_state["last_move_at"] or game_state["current_player_name"] != last_game_state["current_player_name"]:
                    print("Game state has changed.", game_state)
                    file_path.write_text(json.dumps(game_state, indent=4, sort_keys=True))

                    latest_state = json.loads(game["latest_state"])
                    current_nation = ":flag-" + latest_state["currentNation"].lower() + ':'
                    slack_user_id = players.get(game_state["current_player_name"], None)

                    if slack_user_id:
                        r = requests.post(WEBHOOK_URL, json={
                            "text": f"It's <@{slack_user_id}>'s <https://www.playimperial.club/game/{TARGET_GAME_ID}|turn> for {current_nation}."
                        })

                else:
                    print("Game state is the same as before.", game_state)

                break
else:
    print("Failed to fetch the game state.")