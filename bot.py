import requests
import config
import logging
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

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

    matches_info = "Today's Football Matches:\n\n"
    data = response.json()
    if data.get('matches'):
        for match in data['matches']:
            matches_info += f"{match['homeTeam']['name']} vs {match['awayTeam']['name']} at {match['utcDate']}\n"
    else:
        matches_info += "No matches found."

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

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

