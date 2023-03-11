from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask_ngrok import run_with_ngrok
from argument import Argument
import os
import time

from chatgpt import ChatGPT
from database import database

line_bot_api = LineBotApi(Argument.linebot_apt)
line_handler = WebhookHandler(Argument.webhook_secret)

db = database()
app = Flask(__name__)
chatgpt = ChatGPT()

# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.type != "text":
        return
    
    user_id = event.source.user_id
    # print(event)

    db.save_chat(user_id, event.timestamp, 1, event.message.text)

    reply_msg = chatgpt.get_response(user_id).replace("AI:", "", 1)
    db.save_chat(user_id, int(time.time()*1000), 0, reply_msg)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_msg))
    

if __name__ == "__main__":
    # run_with_ngrok(app)
    # app.run(host='0.0.0.0',port=80)
    app.run(host='0.0.0.0',port=8000,ssl_context=('cert\cert.pem', 'cert\privkey.pem'))
