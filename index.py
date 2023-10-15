from flask import Flask, request, abort, render_template, redirect, url_for, send_file
from flask_restx import Api, Resource, fields, reqparse
import werkzeug
from waitress import serve
import os, sys, subprocess, psutil
import shutil
import time
import json, csv
from datetime import datetime
import logging
import threading

sys.path.append('data/')
from Argument import Argument
from Database import database
from MessageHandler import MessageHandler
from APIHandler import APIHandler
from ChatAnalyze import ChatAnalyze
from SystemMigrate import SystemMigrate

from service.llm.Chatgpt import ChatGPT

def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('* %(asctime)s %(levelname)s %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARN)
    console_handler.setFormatter(formatter)

    file_warn_handler = logging.FileHandler('data/system_warn.log', mode='a')
    file_warn_handler.setLevel(logging.WARN) 
    file_warn_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('data/system.log', mode='w')
    file_handler.setLevel(logging.INFO) 
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(file_warn_handler)

setup_logger()

BUILD_VERSION = 'v20231015'

'''
init
'''

def check_environment():
    # set timezone to UTC+8
    process = subprocess.Popen("sudo timedatectl set-timezone Asia/Taipei", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # setup data folder
    folders = ['data','data/flowise','data/cert','static/grafana','resources','resources/image','resources/video','resources/video/img','resources/files']
    for folder in folders:
        os.makedirs(folder, exist_ok=True)

    # create log file
    # if not os.path.isfile('data/system.log'):
    #     open('data/system.log', 'a').close()

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
platform_info = {
    'PLATFORM_NAME':argument.read_conf('system','platform_name'),
    'BUILD_VERSION':BUILD_VERSION,
}

sc = SystemMigrate(db, platform_info)

'''
page definition
'''

app = Flask(__name__)
api = Api(app, version='1.0', title='ChatPlatform API', description='ChatPlatform API for keywords, Story, and other data.', doc='/swagger')

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

    # fix_logger_level()

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

@app.route('/changelog')
def changelog():    
    user_config = apiHandler.check_request_username(request)
    if not user_config:
        return redirect(url_for('login'))
    else:
        (sid,username) = user_config

    # login pass
    PASS_DATA = {'USER_NAME':username,
                 'SID':sid,
                }
    PASS_DATA.update(platform_info)
    return render_template('changelog.html',PASS_DATA=PASS_DATA)

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
                 'MESSAGE_DATA':json.dumps(db.load_recent_chat())
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


# @app.route('/reply_setting')
# def reply_setting():
#     user_config = apiHandler.check_request_username(request)
#     if not user_config:
#         return redirect(url_for('login'))
#     else:
#         (sid,username) = user_config

#     PASS_DATA = {'USER_NAME':username,
#                  'SID':sid,
#                  'DEFAULT_REPLY': "checked" if argument.read_conf('function','default_reply')=='true' else "",
#                  'DEFAULT_REPLY_WORD': argument.read_conf('function','default_reply_word'),
#                  'KEYWORD_REPLY': "checked" if argument.read_conf('function','keyword_reply')=='true' else "",
#                  'STORY_REPLY': "checked" if argument.read_conf('function','story_reply')=='true' else "",
#                  'CHATGPT_REPLY': "checked" if argument.read_conf('function','chatgpt_reply')=='true' else ""
#                 }
#     PASS_DATA.update(platform_info)
#     return render_template('reply_setting.html',PASS_DATA=PASS_DATA)

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

'''
API resources
'''

class Keywords(Resource):    
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']

    def get(self):
        return self.db.load_keyword()

    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('Keyword', {
        'enable': fields.String(default='1', required=True),
        'keyword': fields.String(default='Keyword', required=True),
        'reply': fields.String(default='Reply', required=True),
        'note': fields.String(default='Note', required=True),
    }))
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            if request_argument['enable']!='0' and request_argument['enable']!='1':
                return 'Bad Request',400
            result = self.db.add_keyword(request_argument['enable'],request_argument['keyword'],request_argument['reply'],request_argument['note'])
            if result == None:
                return 'SQL Command Failed', 500
        except KeyError:
            return 'Bad Request',400
        return 'OK',200

class Keyword(Resource):    
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    def delete(self,keyword_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        result = self.db.delete_keyword(keyword_id)
        if result == None:
            return 'SQL Command Failed', 500
        return 'OK',200

# class ExternelAPI(Resource):
#     """This API is use to provide externel API for outside service to use.
#     Currently unusable because of system design!    

#     Args:
#         Resource (_type_): _description_
#     """
#     def __init__(self,db,apiHandler):
#         self.db = db
#         self.apiHandler = apiHandler

class FileAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.baseURL = 'resources/files/'
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('File', {
        'file': fields.Raw(required=True),
    }))
    def post(self,filename):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        if filename == 'undefined':
            return 'No filename',400

        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        file = args['file']
        if file.content_length > 1024*1024*10: # 10MB
            return 'File too large',413

        file.save(self.baseURL+filename)
        return (filename,200)
        
class ImageAPI(Resource):    
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.baseURL = 'resources/image/'
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('Image', {
        'file': fields.Raw(required=True),
    }))
    def post(self,filename):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        image_file = args['file']

        num = self._get_next_filename()
        if not num:
            return ('Image Folder Format Error', 500)

        if image_file.content_type == 'image/png':
            image_file.save(self.baseURL+num+'.png')
            return (num+'.png',200)
        elif image_file.content_type == 'image/jpeg':
            image_file.save(self.baseURL+num+'.jpeg')
            return (num+'.jpeg',200)
        else :
            return ('error',415) 
        
    @api.doc(params={'sid':'sid'})
    def get(self, filename):
        # Logic to fetch or generate the image
        # Replace this with your actual image retrieval code
        filename = self.baseURL + filename

        if os.path.isfile(filename):
            # Use send_file to send the image file
            if filename.endswith('.png'):
                return send_file(filename, mimetype='image/png')
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return send_file(filename, mimetype='image/jpeg')
            else:
                return ('Bad Format', 403)
        else:
            return ('FileNotFound', 404)
        
    def _get_next_filename(self):
        files = os.listdir(self.baseURL)
        if not files:
            return '1'
        try:
            max_num = max([int(file.split(".")[0]) for file in files])
            return str(max_num+1)
        except:
            logging.error('Image Folder Format Error!')
            return None

class LineReachMenu(Resource):
    def __init__(self, *args, **kwargs):
        self.argument = kwargs['argument']
        self.apiHandler = kwargs['apiHandler']
        self.line_platform = kwargs['line_platform']
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('LineReachMenu', {
        'richmenu_id': fields.String(required=True),
        'richmenu_image': fields.String(required=True, description='use ImageAPI first, return filepath here.'),
        'richmenu_json': fields.String(required=True),
        "set_default": fields.String(required=True, default='0'),
    }))
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            if request_argument['richmenu_image']=='' or request_argument['richmenu_json']=='':
                return 'Bad Request',400

            richmenu_id = int(request_argument['richmenu_id'])
            richmenu_image = 'resources/image/' + request_argument['richmenu_image']
            richmenu_json = 'resources/files/' + request_argument['richmenu_json']
            menu_id = self.line_platform.upload_rich_menu(richmenu_image,richmenu_json)

            if not menu_id: # upload rich menu failed
                return 'Bad Request',400

            if int(request_argument['set_default'])==1:
                self.line_platform.set_default_rich_menu(menu_id)

            self.argument.set_conf('line','richmenu_image_'+str(richmenu_id),request_argument['richmenu_image'])
            self.argument.set_conf('line','richmenu_json_'+str(richmenu_id),request_argument['richmenu_json'])
            self.argument.set_conf('line','richmenu_id_'+str(richmenu_id),menu_id)
            return 'OK',200
        
        except KeyError:
            return 'Bad Request',400

class LineMembers(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        return self.db.load_all_user() 

# class ChatSetting(Resource):
#     def __init__(self, *args, **kwargs):
#         self.argument = Argument()
#         self.apiHandler = kwargs['apiHandler']
        
#     def post(self,key):
#         user_config = self.apiHandler.check_request_username(request)
#         if not user_config:
#             return 'Not Authorized',401
#         request_argument = request.get_json()
#         try:
#             if key=='' or request_argument['value']=='':
#                 return 'Bad Request',400
#             self.argument.set_conf('function',key,request_argument['value'])
#         except KeyError:
#             return 'Bad Request',400
#         return 'OK',200

class Story_name(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        return json.dumps(self.db.load_story_name(),ensure_ascii=False) 

class Story_sentence(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    def get(self, story_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        return json.dumps(self.db.load_sentences_from_story(story_id),ensure_ascii=False)
        
    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('Story_sentence', {
        'story_name': fields.String(default='story_name',required=True,),
        'story_content': fields.String(default='story_content',required=True),
    }))
    def post(self,story_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401

        request_argument = request.get_json()
        try:
            story_name =  request_argument['story_name']
            story_content = request_argument['story_content']
            if story_id!="0":
                self._delete_story(story_id)
            self._create_new_story(story_name,story_content)
        except KeyError:
            return 'Bad Request',400
        return 'OK',200
    
    @api.doc(params={'sid':'sid'})
    def delete(self,story_id):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        self._delete_story(story_id)
        return 'OK',200

    def _create_new_story(self, story_name,story_content):
        story_id = self.db.add_story_name(story_name)
        for i in range(len(story_content)):
            sentencce_id = self.db.add_story_sentence(story_id, story_content[i][1], story_content[i][2], story_content[i][3])
            # fix auto fillin sentence id
            for j in range(i,len(story_content)):
                if str(story_content[j][1]) == str(story_content[i][0]):
                    story_content[j][1] = sentencce_id

    def _delete_story(self, story_id):
        self.db.delete_storyname_id(story_id)
        self.db.delete_storysentence_id(story_id)

class SystemConfigFileAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.configURL = 'data/config.conf'
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('SystemConfigFileAPI', {
        'file': fields.Raw(required=True),
    }))
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        file = args['file']

        if file.content_type == 'text/plain' and file.filename == 'config.conf':
            file.save(self.configURL)
            return ('ok',200)
        else:
            return ('error',415)     
        
    @api.doc(params={'sid':'sid'})
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401

        return send_file(self.configURL, mimetype='text/plain')

class SystemMigrateAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        zip_location = sc.export_system_config()
        if not zip_location:
            return 'Internal Server Error',500
        return send_file(zip_location, mimetype='application/zip')
    
    # @api.doc(params={'sid':'sid'})
    # @api.expect(api.model('SystemMigrateAPI', {
    #     'file': fields.Raw(required=True),
    # }))
    # def post(self):
    #     user_config = self.apiHandler.check_request_username(request)
    #     if not user_config:
    #         return 'Not Authorized',401
        
    #     parse = reqparse.RequestParser()
    #     parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    #     args = parse.parse_args()
    #     file = args['file']

    #     if file.content_type not in {'application/zip','application/x-zip-compressed'}:
    #         return ('file type not zip',415)
        
    #     file.save('resources/files/migrate.zip')
    #     result = sc.import_system_config('resources/files/migrate.zip')
    #     if not result:
    #         return ('failed to restore',500)
    #     return ('ok',200)

            
class SystemInfo(Resource):
    def __init__(self, *args, **kwargs):
        self.argument = Argument()
        self.apiHandler = kwargs['apiHandler']  
        self.db = kwargs['db']
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    def get(self):
        system_info = {
            'USER_AMOUNT':db.load_user_amount(),
            'CHAT_AMOUNT':db.load_chat_amount(),
            'OPENAI_USAGE_AMOUNT':db.load_openai_usage(),
            'USAGE_GRAPH_DATA':json.dumps(db.load_chat_amount_each_month()),
        }
        return system_info

class SystemSetting(Resource):
    def __init__(self, *args, **kwargs):
        self.argument = Argument()
        self.apiHandler = kwargs['apiHandler']  
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    def get(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        try:
            with open('data/config.conf','r') as f:
                configs = f.read()
                return configs
        except:
            return 'Internal Server Error',500
    
    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('SystemSetting', {
        'settings': fields.String(required=True,description='system config, change carefully!'),
    }))
    def post(self):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        
        if request_argument['settings']=='':
            return 'Bad Request',400
        else:
            with open('data/config.conf','w') as f:
                f.write(request_argument['settings'])
            self.apiHandler.reload_password_hash()
            # self._restart_program()
            return 'OK',200

    def _restart_program(self):
        """Restarts the current program, with file objects and descriptors
        cleanup
        """
        try:
            p = psutil.Process(os.getpid())
            for handler in p.open_files() + p.connections():
                os.close(handler.fd)
        except Exception as e:
            logging.error(e)

        sys.stdout.flush()
        os.execv(sys.executable, ['python'] + [sys.argv[0]])

@api.doc(description='Ban User')
class User(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    def post(self,UUID):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        request_argument = request.get_json()
        try:
            result = self.db.ban_user(UUID,request_argument['ban'])
            if result == None:
                return 'SQL Command Failed', 500
        except KeyError:
            return 'Bad Request',400
        return 'OK',200

class UserChatHistory(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.api = kwargs['api']

    @api.doc(params={'sid':'sid'})
    def get(self,UUID):
        chat_history = self.db.load_chat_detail(UUID,count=1000)

        if not chat_history:
            return 'Not Found',404

        header = ["messageID", "time", "direction", "text"]
        chat_history.insert(0,header)

        csv_location = '/tmp/data.csv'
        with open(csv_location, mode='w', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            writer.writerows(chat_history)
        return send_file(csv_location, mimetype='application/csv')

class VideoAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.baseURL = 'resources/video/'
        self.videoimgURL = self.baseURL + 'img/'
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    @api.expect(api.model('VideoAPI', {
        'file': fields.Raw(required=True),
    }))
    def post(self,filename):
        user_config = self.apiHandler.check_request_username(request)
        if not user_config:
            return 'Not Authorized',401
        
        parse = reqparse.RequestParser()
        parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
        args = parse.parse_args()
        video_file = args['file']

        num = self._get_next_filename()
        if not num:
            return ('Video Folder Format Error', 500)

        if video_file.content_type == 'video/mp4':
            video_file.save(self.baseURL+num+'.mp4')
            # 生成影片封面縮圖
            os.system('ffmpeg -i '+self.baseURL+num+'.mp4 -ss 00:00:01.000 -vframes 1 '+self.videoimgURL+num+'.jpg')
            return (num+'.mp4',200)
        else :
            return ('error',415) 
        
    def get(self, filename):
        filename = self.baseURL + filename

        if os.path.isfile(filename):
            # Use send_file to send the image file
            if filename.endswith('.mp4'):
                return send_file(filename, mimetype='video/mp4')
            else:
                return ('Bad Format', 403)
        else:
            return ('FileNotFound', 404)
        
    def _get_next_filename(self):
        # get file in path
        files = os.listdir(self.baseURL)
        for file in files:
            if os.path.isdir(self.baseURL + file):
                files.remove(file)
        
        if not files:
            return '1'
        try:
            max_num = max([int(file.split(".")[0]) for file in files])
            return str(max_num+1)
        except Exception as e:
            logging.error('Video Folder Format Error!')
            return None

class VideoThumbnailAPI(Resource):
    def __init__(self, *args, **kwargs):
        self.db = kwargs['db']
        self.apiHandler = kwargs['apiHandler']
        self.baseURL = 'resources/video/img/'
        self.api = kwargs['api']
    
    @api.doc(params={'sid':'sid'})
    def get(self, filename):
        filename = self.baseURL + filename

        if os.path.isfile(filename):
            # Use send_file to send the image file
            if filename.endswith('.jpg') or filename.endswith('.jpeg'):
                return send_file(filename, mimetype='image/jpeg')
            else:
                return ('Bad Format', 403)
        else:
            return ('FileNotFound', 404)


api.add_resource(Keywords, '/api/keywords',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(Keyword, '/api/keyword/<string:keyword_id>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(Story_name, '/api/story_name',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(Story_sentence, '/api/story_sentence/<string:story_id>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(User, '/api/user/<string:UUID>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(UserChatHistory, '/api/user_chat_history/<string:UUID>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(SystemSetting, '/api/system_setting',resource_class_kwargs={'api':api,'apiHandler':apiHandler})
api.add_resource(SystemMigrateAPI, '/api/system_migrate',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(SystemConfigFileAPI, '/api/system_config',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(SystemInfo, '/api/system_info',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(ImageAPI, '/api/image/<string:filename>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(VideoAPI, '/api/video/<string:filename>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(VideoThumbnailAPI, '/api/video_thumbnail/<string:filename>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(FileAPI, '/api/file/<string:filename>',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})
api.add_resource(LineReachMenu, '/api/line/rich_menu',resource_class_kwargs={'api':api,'argument':argument,'apiHandler':apiHandler,'line_platform':line})
api.add_resource(LineMembers, '/api/line/members',resource_class_kwargs={'api':api,'db':db,'apiHandler':apiHandler})

'''
disabled api
'''
# api.add_resource(ChatSetting, '/api/setting/chat/<string:key>',resource_class_kwargs={'apiHandler':apiHandler})

if __name__ == "__main__":
    port = int(argument.read_conf('system','system_port'))
    print('SERVER START UP !')
    if argument.read_conf('system','use_local_certificates') == 'true':
        app.run(host='0.0.0.0',port=port,ssl_context=('data/cert/cert.pem', 'data/cert/privkey.pem'))
    else:
        serve(app, host='0.0.0.0', port=port, threads=10)

