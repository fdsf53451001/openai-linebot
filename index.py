from flask import Flask, request, abort, render_template, redirect, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask_ngrok import run_with_ngrok
import os, sys
import time
import json

sys.path.append('data/')
from argument import Argument
from chatgpt import ChatGPT
from database import database

line_bot_api = LineBotApi(Argument.linebot_apt)
line_handler = WebhookHandler(Argument.webhook_secret)

db = database()
app = Flask(__name__)
chatgpt = ChatGPT()

sid_list = [user[2] for user in Argument.user_list]

# domain root
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/index')
def index():
    args = request.args
    sid = args.get('sid', None)
    if sid==None or sid not in sid_list:
        return redirect(url_for('login'))
    else:
        username = Argument.user_list[sid_list.index(sid)][0]
    
    # login pass
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'USER_AMOUNT':db.load_user_amount(),
                 'CHAT_AMOUNT':db.load_chat_amount(),
                 'USAGE_GRAPH_DATA':json.dumps(db.load_chat_amount_each_month()),
                 'SYSTEM_LOGS':db.load_system_logs()
                }
    return render_template('index.html',PASS_DATA=PASS_DATA)

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

    reply_msg = chatgpt.get_response(user_id)
    if reply_msg != None:
        reply_msg = reply_msg.replace("AI:", "", 1)
        db.save_chat(user_id, int(time.time()*1000), 0, reply_msg)   
    else:
        reply_msg = "RateLimitError!"

    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))
    
@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/check_login", methods=['POST'])
def check_login():
    if request.method != 'POST':
        print('get')
        return redirect(url_for('login'))
    firstname = request.values['username']
    password = request.values['password']

    try:
        index = [user[0] for user in Argument.user_list].index(firstname)
        if password == Argument.user_list[index][1]:
            return redirect(url_for('index',sid=Argument.user_list[index][2]))
    except ValueError:
        pass

    # login fail
    return render_template('login.html',ERROR_MSG="username or password error!")

if __name__ == "__main__":
    # run_with_ngrok(app)
    app.run(host='0.0.0.0',port=8000,debug=True)
    # app.run(host='0.0.0.0',port=8000,ssl_context=('cert\cert.pem', 'cert\privkey.pem'))
