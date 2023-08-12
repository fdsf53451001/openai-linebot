from flask import Flask, request, abort, render_template, redirect, url_for
# from linebot import LineBotApi, WebhookHandler
# from linebot.exceptions import InvalidSignatureError
# from linebot.models import MessageEvent, TextMessage, TextSendMessage
# from flask_ngrok import run_with_ngrok
# from flask_restful import Resource, Api
from flask_restx import Api, Resource
from waitress import serve
import os, sys, subprocess
import shutil
import time
import json
from datetime import datetime
import logging
logging.basicConfig(
                    format='* %(asctime)s %(levelname)s %(message)s',
                    level=logging.WARN , 
                    handlers=[logging.StreamHandler(), logging.FileHandler('data/system.log',delay=True)]
                    )
import threading
sys.path.append('data/')
from Argument import Argument
from Database import database
from MessageHandler import MessageHandler
from APIHandler import APIHandler
from ChatAnalyze import ChatAnalyze

from service.llm.Chatgpt import ChatGPT

from service.api.Keyword import Keywords, Keyword
from service.api.Setting import ChatSetting
from service.api.SystemSetting import SystemSetting
from service.api.SystemConfigAPI import SystemConfigAPI
from service.api.Story import Story_name, Story_sentence
from service.api.User import User
from service.api.ImageAPI import ImageAPI
from service.api.VideoAPI import VideoAPI
from service.api.VideoThumbnailAPI import VideoThumbnailAPI
from service.api.FileAPI import FileAPI
from service.api.LineSetting import LineReachMenu

'''
init
'''

def check_environment():
    # set timezone to UTC+8
    process = subprocess.Popen("sudo timedatectl set-timezone Asia/Taipei", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # create log file
    if not os.path.isfile('data/system.log'):
        open('data/system.log', 'a').close()

    # create config file
    if not os.path.isfile('data/config.conf'):
        shutil.copy('default/config.conf', 'data/config.conf')
    argument = Argument()

    # create database file
    if not os.path.isfile(argument.read_conf('sqlite','db_path')):
        shutil.copy('default/chat.db', argument.read_conf('sqlite','db_path'))
    
    # check environmental variable
    if os.environ.get('SYSTEM_PORT'):
        argument.set_conf('system','system_port',os.environ.get('SYSTEM_PORT'))

    return argument 

argument = check_environment()

# set threading lock prevent sqlite error
db_lock = threading.Lock()
db = database(argument.read_conf('sqlite','db_path'),db_lock)

chatgpt = ChatGPT(db,argument)
messageHandler = MessageHandler(db,chatgpt)
apiHandler = APIHandler(db)

# doing talk emotion analyze, this will take a while
# just for test purpose
if argument.read_conf('openai','analyze_msg_with_openai') == 'true':
    chatAnalyze = ChatAnalyze(db, chatgpt)
    chatAnalyze.search_chat_session()
    chatAnalyze.analyze_with_openai()

if argument.read_conf('platform','line') == 'true':
    from service.chat_platform.line_platform import line_platform
    line = line_platform(argument, messageHandler)
else:
    line = None

# define platform information
platform_info = {'PLATFORM_NAME':argument.read_conf('system','platform_name')}

def talk_test():
    while True:
        user_id = 'command_line'
        receive_text = input('text:')
        receive_timestamp = int(time.time()*1000)
        reply_msg = messageHandler.handdle('command_line',user_id, receive_text, receive_timestamp)
        print('reply:',str(reply_msg))

'''
page definition
'''

app = Flask(__name__)
api = Api(app, version='1.0', title='My API', description='A sample API', doc='/swagger')

# domain root
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route("/webhook", methods=['POST'])
def callback():
    return messageHandler.receive_request('line',request)

@app.route('/index')
def index():    
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    fix_logger_level()

    # login pass
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'USER_AMOUNT':db.load_user_amount(),
                 'CHAT_AMOUNT':db.load_chat_amount(),
                 'OPENAI_USAGE_AMOUNT':db.load_openai_usage(),
                 'USAGE_GRAPH_DATA':json.dumps(db.load_chat_amount_each_month()),
                 'SYSTEM_LOGS':db.load_system_logs()
                }
    PASS_DATA.update(platform_info)
    return render_template('index.html',PASS_DATA=PASS_DATA)

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
    PASS_DATA.update(platform_info)
    return render_template('keyword.html',PASS_DATA=PASS_DATA)

@app.route('/message')
def message_page():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'MESSAGE_DATA':json.dumps(db.load_chat_detail())
                }
    PASS_DATA.update(platform_info)
    return render_template('message.html',PASS_DATA=PASS_DATA)

@app.route('/introduction')
def introduction():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                }
    PASS_DATA.update(platform_info)
    return render_template('introduction.html',PASS_DATA=PASS_DATA)

@app.route('/openai_setting')
def openai_setting():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                }
    PASS_DATA.update(platform_info)
    return render_template('openai_setting.html',PASS_DATA=PASS_DATA)

@app.route('/qna')
def qna():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                }
    PASS_DATA.update(platform_info)
    return render_template('QNA.html',PASS_DATA=PASS_DATA)


@app.route('/user_list')
def user_list():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'USERS_DATA':json.dumps(db.load_all_user())
                }
    PASS_DATA.update(platform_info)
    return render_template('user_list.html',PASS_DATA=PASS_DATA)

@app.route('/talk_analyze')
def talk_analyze():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config
    
    if argument.read_conf('system','grafana_domain') != 'None':
        ChatAnalyze.get_grafana_analyze_image(argument)

    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                 'GRAFANA_DOMAIN':argument.read_conf('system','grafana_domain'),
                 'GRAFANA_IMAGE_AMOUNT':int(argument.read_conf('grafana','image_amount'))
                }
    PASS_DATA.update(platform_info)
    return render_template('talk_analyze.html',PASS_DATA=PASS_DATA)


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
                 'STORY_REPLY': "checked" if argument.read_conf('function','story_reply')=='true' else "",
                 'CHATGPT_REPLY': "checked" if argument.read_conf('function','chatgpt_reply')=='true' else ""
                }
    PASS_DATA.update(platform_info)
    return render_template('reply_setting.html',PASS_DATA=PASS_DATA)

@app.route('/api_setting')
def api_setting():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                #  'DEFAULT_REPLY': "checked" if argument.read_conf('function','default_reply')=='true' else "",
                #  'DEFAULT_REPLY_WORD': argument.read_conf('function','default_reply_word'),
                #  'KEYWORD_REPLY': "checked" if argument.read_conf('function','keyword_reply')=='true' else "",
                #  'STORY_REPLY': "checked" if argument.read_conf('function','story_reply')=='true' else "",
                #  'CHATGPT_REPLY': "checked" if argument.read_conf('function','chatgpt_reply')=='true' else ""
                }
    PASS_DATA.update(platform_info)
    return render_template('api_setting.html',PASS_DATA=PASS_DATA)

@app.route('/line_setting')
def line_setting():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                }
    PASS_DATA.update(platform_info)
    return render_template('line_setting.html',PASS_DATA=PASS_DATA)

@app.route('/story')
def story():
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    PASS_DATA = {'USER_NAME':username,
                 'SID':sid
                }
    PASS_DATA.update(platform_info)
    return render_template('story.html',PASS_DATA=PASS_DATA)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route("/check_login", methods=['POST'])
def check_login():
    if request.method != 'POST':
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
    PASS_DATA.update(platform_info)
    return render_template('404.html',PASS_DATA=PASS_DATA)  # 錯誤回傳

def fix_logger_level():
    # set global logger level
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for logger in loggers:
        logger.setLevel(logging.WARNING)

api.add_resource(Keywords, '/api/keywords',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(Keyword, '/api/keyword/<string:keyword_id>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(ChatSetting, '/api/setting/chat/<string:key>',resource_class_kwargs={'apiHandler':apiHandler})
api.add_resource(Story_name, '/api/story_name',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(Story_sentence, '/api/story_sentence/<string:story_id>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(User, '/api/user/<string:UUID>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(SystemSetting, '/api/system_setting',resource_class_kwargs={'apiHandler':apiHandler})
api.add_resource(ImageAPI, '/api/image/<string:filename>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(VideoAPI, '/api/video/<string:filename>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(VideoThumbnailAPI, '/api/video_thumbnail/<string:filename>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(SystemConfigAPI, '/api/system_config',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(FileAPI, '/api/file/<string:filename>',resource_class_kwargs={'db':db,'apiHandler':apiHandler})
api.add_resource(LineReachMenu, '/api/line/rich_menu',resource_class_kwargs={'argument':argument,'apiHandler':apiHandler,'line_platform':line})


if __name__ == "__main__":
    # local test will block command line, prevent web page to load
    local_test = False
    port = int(argument.read_conf('system','system_port'))

    print('SERVER START UP !')
    if local_test:
        talk_test()
    elif argument.read_conf('system','use_local_certificates') == 'true':
        app.run(host='0.0.0.0',port=port,ssl_context=('data/cert/cert.pem', 'data/cert/privkey.pem'))
    else:
        serve(app, host='0.0.0.0', port=port, threads=10)

