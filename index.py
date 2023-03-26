from flask import Flask, request, abort, render_template, redirect, url_for
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask_ngrok import run_with_ngrok
from flask_restful import Resource, Api
import os, sys
import time
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

sys.path.append('data/')
sys.path.append('api/')
from Argument import Argument
from chatgpt import ChatGPT
from database import database
from MessageHandler import MessageHandler
from APIHandler import APIHandler

from Keyword import Keywords, Keyword
from Setting import ChatSetting

argument = Argument()
line_bot_api = LineBotApi(argument.linebot_apt)
line_handler = WebhookHandler(argument.webhook_secret)

db = database()
chatgpt = ChatGPT(db,argument.openai_key)
messageHandler = MessageHandler(db,chatgpt)
apiHandler = APIHandler(db)

app = Flask(__name__)
api = Api(app)

# domain root
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/index')
def index():    
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

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
    # app.logger.info("Request body: " + body)
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
    receive_text = event.message.text
    receive_timestamp = event.timestamp

    logging.info('receive from %s %s',user_id,receive_text)

    reply_msg = messageHandler.handdle(user_id, receive_text, receive_timestamp)

    logging.info('reply to %s %s',user_id,reply_msg)
    line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))

@app.route('/keyword')
def keyword_page():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'KEYWORD_DATA':json.dumps(db.load_keyword())
                }
    return render_template('keyword.html',PASS_DATA=PASS_DATA)

@app.route('/reply_setting')
def reply_setting():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'DEFAULT_REPLY': "checked" if argument.read_conf('function','default_reply')=='true' else "",
                 'DEFAULT_REPLY_WORD': argument.read_conf('function','default_reply_word'),
                 'KEYWORD_REPLY': "checked" if argument.read_conf('function','keyword_reply')=='true' else "",
                 'CHATGPT_REPLY': "checked" if argument.read_conf('function','chatgpt_reply')=='true' else ""
                }
    return render_template('reply_setting.html',PASS_DATA=PASS_DATA)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/check_login", methods=['POST'])
def check_login():
    if request.method != 'POST':
        print('get')
        return redirect(url_for('login'))
    username = request.values['username']
    password = request.values['password']

    sessionID = apiHandler.user_login(username, password)
    if sessionID:
        return redirect(url_for('index',sid=sessionID))
    else:
        # login fail
        return render_template('login.html',ERROR_MSG="username or password error!")



@app.route("/action", methods=['POST'])
def action():
    return None

@app.errorhandler(404)
def page_not_found(error):
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'KEYWORD_DATA':json.dumps(db.load_keyword())
                }
    return render_template('404.html',PASS_DATA=PASS_DATA)  # 錯誤回傳

api.add_resource(Keywords, '/api/keywords',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(Keyword, '/api/keyword/<string:keyword_id>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(ChatSetting, '/api/setting/chat/<string:key>',resource_class_kwargs={'apiHandler':apiHandler})

if __name__ == "__main__":
    # run_with_ngrok(app)
    app.run(host='0.0.0.0',port=8000,debug=True)
    # app.run(host='0.0.0.0',port=443,ssl_context=('cert/cert.pem', 'cert/privkey.pem'))
