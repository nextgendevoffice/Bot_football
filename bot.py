import requests
import config
import logging
import pytz
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

line_bot_api = LineBotApi(config.LINE_ACCESS_TOKEN)
handler = WebhookHandler(config.LINE_CHANNEL_SECRET)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_todays_matches():
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"http://api.football-data.org/v2/matches?dateFrom={today}&dateTo={today}"
    headers = {'X-Auth-Token': config.FOOTBALL_API_KEY}
    response = requests.get(url, headers=headers)
    logging.info(f"API Response: {response.json()}") # Log the API response

    data = response.json()
    matches_by_league = {}

    if data.get('matches'):
        for match in data['matches']:
            league_name = match['competition']['name']
            if league_name not in matches_by_league:
                matches_by_league[league_name] = []

            # Convert UTC to Thailand Time (UTC+7)
            utc_time = datetime.fromisoformat(match['utcDate'].rstrip('Z'))
            thailand_time = utc_time + timedelta(hours=7)
            formatted_time = thailand_time.strftime('%Y-%m-%d %H:%M:%S')

            match_info = f"ทีมเหย้า: {match['homeTeam']['name']} vs {match['awayTeam']['name']} ทีมเยือน\nวันเวลา: {formatted_time}\n"
            matches_by_league[league_name].append(match_info)

        matches_info = "Today's Football Matches:\n\n"
        for league, matches in matches_by_league.items():
            matches_info += f"League: {league}\n"
            matches_info += "".join(matches) + "\n"
    else:
        matches_info = "วันนี้ไม่มีการแข่งขัน."

    return matches_info

def get_yesterdays_matches():
    yesterday = datetime.now() - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')
    url = f"http://api.football-data.org/v2/matches?dateFrom={date_str}&dateTo={date_str}"
    headers = {'X-Auth-Token': config.FOOTBALL_API_KEY}
    response = requests.get(url, headers=headers)
    logging.info(f"API Response: {response.json()}") # Log the API response

    data = response.json()
    matches_by_league = {}

    if data.get('matches'):
        for match in data['matches']:
            league_name = match['competition']['name']
            if league_name not in matches_by_league:
                matches_by_league[league_name] = []

            # Convert UTC to Thailand Time (UTC+7)
            utc_time = datetime.fromisoformat(match['utcDate'].rstrip('Z'))
            thailand_time = utc_time + timedelta(hours=7)
            formatted_time = thailand_time.strftime('%Y-%m-%d %H:%M:%S')

            # Assuming 'score' is part of the response data structure
            score = f"{match['score']['fullTime']['homeTeam']} - {match['score']['fullTime']['awayTeam']}"
            match_info = f"ทีมเหย้า: {match['homeTeam']['name']} vs {match['awayTeam']['name']} ทีมเยือน\nScore: {score}\n"
            matches_by_league[league_name].append(match_info)

        matches_info = "Yesterday's Football Results:\n\n"
        for league, matches in matches_by_league.items():
            matches_info += f"League: {league}\n"
            matches_info += "".join(matches) + "\n"
    else:
        matches_info = "ไม่มีผลการแข่งขัน."

    return matches_info

@app.route("/callback", methods=['POST'])
def callback():
    # Get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # Get request body as text
    body = request.get_data(as_text=True)

    # Handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "ตารางบอล":
        matches_info = get_todays_matches()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=matches_info)
        )
    elif event.message.text == "ผลบอล":
        results_info = get_yesterdays_matches()
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=results_info)
        )
# Initialize scheduler
scheduler = BackgroundScheduler()

def scheduled_task():
    # Logic to check for new results and send notifications
    results_info = get_yesterdays_matches()  # or another function to fetch latest results
    line_bot_api.broadcast(TextSendMessage(text=results_info))  # Broadcast to all users

# Add the scheduled task
scheduler.add_job(scheduled_task, 'interval', minutes=1)  # Adjust the interval as needed
scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

