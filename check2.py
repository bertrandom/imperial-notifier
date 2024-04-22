import psycopg2
import psycopg2.extras
import requests
from appcfg import get_config

config = get_config(__name__)

TARGET_GAME_ID = config["target_game_id"]
WEBHOOK_URL = config["slack_webhook_url"]

players = config["players"]

conn = psycopg2.connect(config["postgres_dsn"])
cur = conn.cursor()
cur.execute("SELECT id, rendered_string FROM gamelog WHERE game_id = %s AND broadcast = FALSE ORDER BY log_timestamp", (TARGET_GAME_ID,))
records = cur.fetchall()

if len(records) > 0:
    text = ""

    for record in records:
        text += record[1] + "\n"
        result = cur.execute("UPDATE gamelog SET broadcast = TRUE WHERE id = %s", (record[0],))

    conn.commit()

    print(text)

    r = requests.post(WEBHOOK_URL, json={
        "text": text
    })

cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("SELECT * FROM games WHERE game_id = %s", (TARGET_GAME_ID,))
record = cur.fetchone()

if record:
    if (record['current_player_name'] != record['last_player_broadcast']):
        current_nation = ":flag-" + record['current_nation'].lower() + ':'
        slack_user_id = players.get(record['current_player_name'], None)
        if slack_user_id:

            if record['has_control']:
                text = f"It's <@{slack_user_id}>'s <https://www.playimperial.club/game/{TARGET_GAME_ID}|turn> for {current_nation}."
            else:
                text = f"It's <@{slack_user_id}>'s <https://www.playimperial.club/game/{TARGET_GAME_ID}|turn>."

            print(text)

            r = requests.post(WEBHOOK_URL, json={
                "text": text
            })

            if r.status_code == 200:
                cur.execute("UPDATE games SET last_player_broadcast = %s WHERE game_id = %s", (record['current_player_name'], TARGET_GAME_ID))
                conn.commit()